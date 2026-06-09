"""FastAPI application — aesthetic training agent system MVP."""

import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Callable, TypeVar

from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    OpenAIError,
)
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.analyzer import AnalyzerAgent
from app.agents.comparator import ComparatorAgent
from app.agents.critic import CriticAgent
from app.agents.iterator import IteratorAgent
from app.agents.profile import ProfileAgent
from app.agents.prompt_generator import PromptGeneratorAgent
from app.agents.reference_comparator import ReferenceComparatorAgent
from app.agents.weekly_review import WeeklyReviewAgent
from app.db.database import get_db, init_db
from app.llm.deepseek_client import (
    get_deepseek_client,
    get_default_model,
    get_reasoning_model,
)
from app.schemas.requests import (
    CompareWithReferencesRequest,
    CompleteTrainingRequest,
    GeneratePromptRequest,
    ReferenceCaseCreate,
    WorkDescriptionRequest,
)
from app.schemas.responses import (
    AnalyzeResponse,
    AssessmentOverview,
    AssessmentReport,
    CaseAuditResponse,
    CompareWithReferencesResponse,
    CritiqueResponse,
    DimensionAssessment,
    GeneratedPrompt,
    ImageDescribeResponse,
    IterateResponse,
    JudgmentGap,
    MistakePattern,
    ProfileResponse,
    RecordType,
    ReferenceCaseListResponse,
    ReferenceCaseResponse,
    SessionDetailResponse,
    SessionRecord,
    SessionsResponse,
    TodayTrainingResponse,
    TRAINING_THEMES,
    TrainingStatsResponse,
    UploadResponse,
    VisionDescription,
    VisionStatusResponse,
    WeeklyReviewResponse,
)
from app.services import session_service, reference_service
from app.services.case_quality import compute_completeness_score, get_missing_fields, is_training_ready
from app.settings.config_store import get_config, get_value, get_vision_missing_keys, get_vision_provider, is_vision_configured
from app.vision.base import VisionAdapter
from app.vision.manual_adapter import ManualAdapter
from app.vision.openai_adapter import OpenAIVisionAdapter
from app.vision.placeholder_adapter import PlaceholderAdapter

AgentResultT = TypeVar("AgentResultT")


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


# ── App factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Aesthetic Training Agent System",
    description="MVP backend for AI-assisted aesthetic judgment training",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow the Next.js dev server (and any other frontend) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images so the frontend can preview them.
_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parent.parent / "data" / "uploads")))
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")

# ── Settings router (V1.7 BYOK) ───────────────────────────────────────
from app.settings.routes import router as settings_router  # noqa: E402
app.include_router(settings_router)


# ── Agent dependencies ────────────────────────────────────────────────

def _get_client():
    try:
        return get_deepseek_client()
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail="DeepSeek API key is not configured. Set DEEPSEEK_API_KEY.",
        ) from exc


def _get_model():
    return get_default_model()


def _get_reasoning_model():
    return get_reasoning_model()


def get_analyzer(
    client=Depends(_get_client),
    model=Depends(_get_model),
) -> AnalyzerAgent:
    return AnalyzerAgent(client=client, model=model)


def get_critic(
    client=Depends(_get_client),
    model=Depends(_get_model),
) -> CriticAgent:
    return CriticAgent(client=client, model=model)


def get_iterator(
    client=Depends(_get_client),
    model=Depends(_get_model),
) -> IteratorAgent:
    return IteratorAgent(client=client, model=model)


def get_profile_agent(
    client=Depends(_get_client),
    reasoning_model=Depends(_get_reasoning_model),
) -> ProfileAgent:
    return ProfileAgent(client=client, model=reasoning_model)


def get_vision_adapter() -> VisionAdapter:
    """Return the current vision adapter based on VISION_PROVIDER env var.

    Supported values:
    - ``placeholder`` (default) — mock structured descriptions, no API key needed
    - ``manual`` — user provides image_description (V1.2 compat)
    - ``openai`` — OpenAI GPT-4o Vision (requires OPENAI_API_KEY)
    - ``claude`` — (future) Claude Vision
    - ``gemini`` — (future) Google Gemini Vision

    Priority: config_store > .env
    """
    provider = (
        get_value("vision", "provider", env_var="VISION_PROVIDER")
        or "placeholder"
    ).strip().lower()
    if provider == "manual":
        return ManualAdapter()
    if provider == "openai":
        api_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY")
        model = get_value("vision", "openai_vision_model", env_var="OPENAI_VISION_MODEL")
        return OpenAIVisionAdapter(api_key=api_key, model=model)
    # Default to placeholder for unknown values
    return PlaceholderAdapter()


def get_comparator(
    client=Depends(_get_client),
    reasoning_model=Depends(_get_reasoning_model),
) -> ComparatorAgent:
    return ComparatorAgent(client=client, model=reasoning_model)


def get_reference_comparator(
    client=Depends(_get_client),
    reasoning_model=Depends(_get_reasoning_model),
) -> ReferenceComparatorAgent:
    return ReferenceComparatorAgent(client=client, model=reasoning_model)


def get_prompt_generator(
    client=Depends(_get_client),
    reasoning_model=Depends(_get_reasoning_model),
) -> PromptGeneratorAgent:
    return PromptGeneratorAgent(client=client, model=reasoning_model)


def get_weekly_reviewer(
    client=Depends(_get_client),
    reasoning_model=Depends(_get_reasoning_model),
) -> WeeklyReviewAgent:
    return WeeklyReviewAgent(client=client, model=reasoning_model)


def _run_agent(operation: str, runner: Callable[[], AgentResultT]) -> AgentResultT:
    try:
        return runner()
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{operation} returned an invalid structured response.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{operation} returned invalid JSON.",
        ) from exc
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{operation} failed while contacting DeepSeek.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{operation} failed. Please try again later.",
        ) from exc


def _vision_http_exception(exc: Exception) -> HTTPException:
    """Map Vision adapter failures to safe, actionable API errors."""
    if isinstance(exc, (json.JSONDecodeError, ValidationError)):
        return HTTPException(
            status_code=502,
            detail="OpenAI Vision 返回格式不是预期 JSON，请稍后重试。",
        )
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(
            status_code=404,
            detail="图片文件不存在，请重新上传后再试。",
        )
    if isinstance(exc, AuthenticationError):
        return HTTPException(
            status_code=401,
            detail="OpenAI API Key 无效或已失效，请在设置页重新保存 Key 后再试。",
        )
    if isinstance(exc, APIConnectionError):
        return HTTPException(
            status_code=502,
            detail="无法连接 OpenAI Vision 服务，请检查本机网络、代理或稍后重试。",
        )
    if isinstance(exc, BadRequestError):
        return HTTPException(
            status_code=400,
            detail="OpenAI Vision 拒绝了这张图片或当前模型参数，请确认图片格式有效且模型支持图片输入。",
        )
    if isinstance(exc, APIStatusError):
        if exc.status_code == 429:
            detail = "OpenAI Vision 请求被限流或额度不足，请检查账号额度后稍后重试。"
        else:
            detail = "OpenAI Vision 服务返回异常状态，请稍后重试。"
        return HTTPException(status_code=502, detail=detail)
    if isinstance(exc, OpenAIError):
        return HTTPException(
            status_code=502,
            detail="OpenAI Vision 调用失败，请检查 Vision 配置或稍后重试。",
        )
    return HTTPException(
        status_code=502,
        detail="视觉适配器调用失败，请检查 Vision 配置或稍后重试。",
    )


def _save_record(
    db: Session,
    record_type: RecordType,
    work_description: str,
    result: AgentResultT,
    **judgment_kwargs: Any,
) -> None:
    try:
        session_service.save_record(
            db,
            record_type=record_type,
            work_description=work_description,
            result=result,
            **judgment_kwargs,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not save the training session.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not save the training session.",
        ) from exc


# ── Upload helpers ────────────────────────────────────────────────────

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MiB


def _extract_ai_summary(result: Any) -> dict[str, Any]:
    """Extract a compact AI evaluation dict from any agent result type."""
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif hasattr(result, "dict"):
        data = result.dict()
    else:
        data = result
    # Remove judgment_gap to avoid recursion
    data.pop("judgment_gap", None)
    return data


def _process_user_judgment(
    request: WorkDescriptionRequest,
    ai_result: Any,
    comparator: ComparatorAgent,
) -> tuple[JudgmentGap | None, dict[str, Any]]:
    """If the request carries user_judgment, run comparator and return
    (gap, judgment_kwargs).  Judgment kwargs are empty when no user_judgment
    is present — pass them to ``_save_record`` as ``**kwargs``.
    """
    if request.user_judgment is None:
        return None, {}

    uj = request.user_judgment
    ai_data = _extract_ai_summary(ai_result)

    # ── Extract AI score from critique-style results ───────────────
    ai_score: int | None = None
    ai_problems: str | None = None
    ai_fixes: str | None = None
    if isinstance(ai_data, dict):
        ts = ai_data.get("total_score")
        if ts is not None:
            ai_score = int(round(float(ts) * 10))  # 1-10 → 10-100
        issues = ai_data.get("main_issues", [])
        if issues:
            ai_problems = "; ".join(issues) if isinstance(issues, list) else str(issues)
        fixes = ai_data.get("priority_fixes", [])
        if fixes:
            ai_fixes = "; ".join(fixes) if isinstance(fixes, list) else str(fixes)

    # ── Run comparator ────────────────────────────────────────────
    gap = _run_agent(
        "Judgment comparison",
        lambda: comparator.run(
            work_description=request.work_description,
            user_judgment=uj.model_dump(),
            ai_result=ai_data,
        ),
    )

    import json as _json
    kwargs: dict[str, Any] = {
        "user_score": uj.score,
        "user_strengths": _json.dumps(uj.strengths, ensure_ascii=False) if uj.strengths else None,
        "user_weaknesses": _json.dumps(uj.weaknesses, ensure_ascii=False) if uj.weaknesses else None,
        "user_priority_fixes": _json.dumps(uj.priority_fixes, ensure_ascii=False) if uj.priority_fixes else None,
        "user_target_audience": uj.target_audience,
        "user_price_band": uj.price_band,
        "ai_score": ai_score,
        "ai_main_problems": ai_problems,
        "ai_priority_fixes": ai_fixes,
        "judgment_gap_summary": gap.short_summary,
        "training_focus_tags": _json.dumps(gap.next_training_focus, ensure_ascii=False) if gap.next_training_focus else None,
    }
    return gap, kwargs


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: WorkDescriptionRequest,
    agent: AnalyzerAgent = Depends(get_analyzer),
    vision: VisionAdapter = Depends(get_vision_adapter),
    comparator: ComparatorAgent = Depends(get_comparator),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Analyze a work description across 9 aesthetic dimensions.

    Optionally accepts image_id + image_description (V1.2) and
    user_judgment (V1.1 training loop).
    """
    image_description = _resolve_image_description(request, vision, db)

    result = _run_agent(
        "LLM analysis",
        lambda: agent.run(
            request.work_description,
            image_description=image_description,
        ),
    )

    # ── Optional judgment gap (V1.1) ──────────────────────────────
    gap, j_kwargs = _process_user_judgment(request, result, comparator)
    _save_record(db, "analyze", request.work_description, result, **j_kwargs)

    if gap is not None:
        return result.model_copy(update={"judgment_gap": gap})
    return result


def _resolve_image_description(
    request: WorkDescriptionRequest,
    vision: VisionAdapter,
    db: Session,
) -> str | None:
    """Resolve an image description from image_id + image_description request fields."""
    if request.image_id is None:
        return None

    uploaded = session_service.get_image_by_id(db, request.image_id)
    if uploaded is None:
        raise HTTPException(
            status_code=404,
            detail=f"Image with id={request.image_id} not found.",
        )

    if request.image_description:
        manual_description = request.image_description.strip()
        if manual_description:
            return manual_description

    try:
        return vision.describe_image(
            uploaded.file_path,
            hint=request.image_description,
        )
    except Exception as exc:
        raise _vision_http_exception(exc) from exc


@app.post("/critique", response_model=CritiqueResponse)
def critique(
    request: WorkDescriptionRequest,
    agent: CriticAgent = Depends(get_critic),
    vision: VisionAdapter = Depends(get_vision_adapter),
    comparator: ComparatorAgent = Depends(get_comparator),
    db: Session = Depends(get_db),
) -> CritiqueResponse:
    """Critique a work with dimension scores, issues, and priority fixes.

    Optionally accepts image_id + image_description (V1.2) to include
    image context in the critique.
    """
    image_description = _resolve_image_description(request, vision, db)
    result = _run_agent(
        "LLM critique",
        lambda: agent.run(request.work_description, image_description=image_description),
    )
    gap, j_kwargs = _process_user_judgment(request, result, comparator)
    _save_record(db, "critique", request.work_description, result, **j_kwargs)

    if gap is not None:
        return result.model_copy(update={"judgment_gap": gap})
    return result


@app.post("/iterate", response_model=IterateResponse)
def iterate(
    request: WorkDescriptionRequest,
    agent: IteratorAgent = Depends(get_iterator),
    vision: VisionAdapter = Depends(get_vision_adapter),
    comparator: ComparatorAgent = Depends(get_comparator),
    db: Session = Depends(get_db),
) -> IterateResponse:
    """Generate 3-5 distinct iteration directions for a work.

    Optionally accepts image_id + image_description (V1.2) to include
    image context in the iteration suggestions.
    """
    image_description = _resolve_image_description(request, vision, db)
    result = _run_agent(
        "LLM iteration",
        lambda: agent.run(request.work_description, image_description=image_description),
    )
    gap, j_kwargs = _process_user_judgment(request, result, comparator)
    _save_record(db, "iterate", request.work_description, result, **j_kwargs)

    if gap is not None:
        return result.model_copy(update={"judgment_gap": gap})
    return result


@app.get("/profile", response_model=ProfileResponse)
def profile(
    agent: ProfileAgent = Depends(get_profile_agent),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    """Summarize user aesthetic profile from recent training history."""
    total = session_service.get_record_count(db)
    history = session_service.get_history_for_profile(db)

    return _run_agent("LLM profile", lambda: agent.run(history, total_sessions=total))


@app.get("/sessions", response_model=SessionsResponse)
def sessions(
    record_type: Annotated[
        RecordType | None,
        Query(description="Optional filter: analyze, critique, or iterate."),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
) -> SessionsResponse:
    """Return recent training session records."""
    records = session_service.get_recent_records(
        db, limit=limit, record_type=record_type
    )
    session_records = [
        SessionRecord(
            id=r.id,
            record_type=r.record_type,
            work_description=r.work_description,
            created_at=r.created_at,
            user_score=r.user_score,
            ai_score=r.ai_score,
            judgment_gap_summary=r.judgment_gap_summary,
            training_focus_tags=r.training_focus_tags,
        )
        for r in records
    ]
    return SessionsResponse(sessions=session_records, total=len(session_records))


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    """Return full detail for a single training session."""
    record = session_service.get_session_by_id(db, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return SessionDetailResponse(
        id=record.id,
        record_type=record.record_type,  # type: ignore[arg-type]
        work_description=record.work_description,
        created_at=record.created_at,
        user_score=record.user_score,
        user_strengths=record.user_strengths,
        user_weaknesses=record.user_weaknesses,
        user_priority_fixes=record.user_priority_fixes,
        user_target_audience=record.user_target_audience,
        user_price_band=record.user_price_band,
        result_json=record.result_json,
        ai_score=record.ai_score,
        ai_main_problems=record.ai_main_problems,
        ai_priority_fixes=record.ai_priority_fixes,
        judgment_gap_summary=record.judgment_gap_summary,
        training_focus_tags=record.training_focus_tags,
        selected_direction=record.selected_direction,
        prompt_result=record.prompt_result,
    )


@app.post("/upload", response_model=UploadResponse, status_code=201)
def upload_image(
    file: Annotated[UploadFile, File(description="Image file: jpg, png, or webp")],
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload an image. Stores the file on disk and returns its metadata.

    Accepted formats: jpg, jpeg, png, webp. Max size: 10 MiB.
    """
    original_filename = file.filename or "unknown"

    # ── Validate extension ──────────────────────────────────────────
    suffix = Path(original_filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{suffix}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}.",
        )

    # ── Validate content type ───────────────────────────────────────
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{content_type}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}.",
        )

    # ── Read & validate size ────────────────────────────────────────
    contents = file.file.read()
    size_bytes = len(contents)
    if size_bytes > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_bytes} bytes). "
            f"Maximum is {_MAX_FILE_SIZE} bytes (10 MiB).",
        )

    # ── Save to disk with a UUID-based filename ─────────────────────
    stored_filename = f"{uuid.uuid4().hex}{suffix}"
    dest = _UPLOAD_DIR / stored_filename
    dest.write_bytes(contents)

    # ── Persist metadata ────────────────────────────────────────────
    try:
        image = session_service.save_image(
            db,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(dest.resolve()),
            content_type=content_type,
            size_bytes=size_bytes,
        )
    except Exception:
        if dest.exists():
            dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save image metadata.",
        )

    return UploadResponse(
        image_id=image.id,
        filename=image.stored_filename,
        content_type=image.content_type,
        size_bytes=image.size_bytes,
        url=f"/uploads/{image.stored_filename}",
        created_at=image.created_at,
    )


@app.post(
    "/images/{image_id}/describe",
    response_model=ImageDescribeResponse,
)
def describe_image(
    image_id: int,
    vision: VisionAdapter = Depends(get_vision_adapter),
    db: Session = Depends(get_db),
) -> ImageDescribeResponse:
    """Auto-generate a structured description for a previously uploaded image.

    Calls the configured ``VisionAdapter.describe_image_structured()``.
    The result is saved to the image record so it can be reused.
    """
    uploaded = session_service.get_image_by_id(db, image_id)
    if uploaded is None:
        raise HTTPException(status_code=404, detail=f"Image id={image_id} not found.")

    try:
        desc = vision.describe_image_structured(uploaded.file_path)
    except Exception as exc:
        raise _vision_http_exception(exc) from exc

    # Persist the description on the image record
    import json as _json
    provider = get_value("vision", "provider", env_var="VISION_PROVIDER") or "placeholder"
    session_service.update_image_description(
        db,
        image_id=image_id,
        ai_description=desc.suggested_prompt_text,
        vision_provider=provider,
        vision_description_json=_json.dumps(desc.model_dump(), ensure_ascii=False),
    )

    is_placeholder = provider not in ("openai", "claude", "gemini") or provider == "placeholder"
    warning = (
        "当前使用占位视觉描述，未调用真实视觉模型。返回的描述为示例数据，不匹配实际图片。"
        if is_placeholder
        else None
    )
    return ImageDescribeResponse(
        image_id=image_id,
        description=desc,
        vision_provider=provider,
        is_placeholder=is_placeholder,
        warning=warning,
    )


@app.get("/vision/status", response_model=VisionStatusResponse)
def vision_status() -> VisionStatusResponse:
    """Return the current vision provider configuration status."""
    provider = get_vision_provider()
    is_placeholder = provider == "placeholder"

    if is_placeholder:
        return VisionStatusResponse(
            vision_provider="placeholder",
            is_placeholder=True,
            is_configured=True,
            missing_keys=[],
            message="当前使用占位视觉描述，不是真实图片识别。返回的描述为固定示例，不匹配实际图片。",
        )

    missing = get_vision_missing_keys(provider)
    labels = {"manual": "Manual Vision", "openai": "OpenAI Vision", "claude": "Claude Vision", "gemini": "Gemini Vision"}

    if missing:
        return VisionStatusResponse(
            vision_provider=provider,
            is_placeholder=False,
            is_configured=False,
            missing_keys=missing,
            message=f"未配置 {', '.join(missing)}，请在后端 .env 或设置页中配置后再使用 {labels.get(provider, provider)}。",
        )

    return VisionStatusResponse(
        vision_provider=provider,
        is_placeholder=False,
        is_configured=True,
        missing_keys=[],
        message=f"{labels.get(provider, provider)} 已配置",
    )


# ── V1.4: Reference Cases ────────────────────────────────────────────

def _ref_response(case, db):
    """Build ReferenceCaseResponse with image_url and V1.9 quality fields."""
    image_url = None
    if case.image_id:
        img = session_service.get_image_by_id(db, case.image_id)
        if img:
            image_url = f"/uploads/{img.stored_filename}"
    return ReferenceCaseResponse(
        id=case.id, title=case.title, category=case.category,
        aesthetic_level=case.aesthetic_level, style_tags=case.style_tags,
        target_audience=case.target_audience, price_band=case.price_band,
        image_id=case.image_id, image_url=image_url,
        image_description=case.image_description, ai_description=case.ai_description,
        notes=case.notes, score=case.score,
        premium_sources=case.premium_sources, cheapness_sources=case.cheapness_sources,
        learn_from_this=case.learn_from_this, avoid_copying=case.avoid_copying,
        created_at=case.created_at, updated_at=case.updated_at,
        completeness_score=compute_completeness_score(case),
        is_training_ready=is_training_ready(case),
        missing_fields=get_missing_fields(case),
    )

@app.post("/reference-cases", response_model=ReferenceCaseResponse, status_code=201)
def create_reference_case(
    body: ReferenceCaseCreate,
    db: Session = Depends(get_db),
) -> ReferenceCaseResponse:
    """Create a new reference case for the aesthetic comparison library."""
    from datetime import datetime as dt

    case = reference_service.create_case(
        db,
        title=body.title,
        category=body.category,
        aesthetic_level=body.aesthetic_level,
        style_tags=body.style_tags,
        target_audience=body.target_audience,
        price_band=body.price_band,
        image_id=body.image_id,
        image_description=body.image_description,
        ai_description=body.ai_description,
        notes=body.notes,
        score=body.score,
        premium_sources=body.premium_sources,
        cheapness_sources=body.cheapness_sources,
        learn_from_this=body.learn_from_this,
        avoid_copying=body.avoid_copying,
        created_at=dt.utcnow(),
        updated_at=dt.utcnow(),
    )
    return _ref_response(case, db)


@app.get("/reference-cases", response_model=ReferenceCaseListResponse)
def list_reference_cases(
    category: str | None = Query(default=None),
    aesthetic_level: str | None = Query(default=None),
    style_tag: str | None = Query(default=None),
    price_band: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ReferenceCaseListResponse:
    """List reference cases with optional filters."""
    cases = reference_service.list_cases(
        db,
        category=category,
        aesthetic_level=aesthetic_level,
        style_tag=style_tag,
        price_band=price_band,
        limit=limit,
    )
    return ReferenceCaseListResponse(
        cases=[_ref_response(c, db) for c in cases],
        total=len(cases),
    )


# ── V1.9: Case quality audit ──────────────────────────────────────────

@app.get("/reference-cases/audit", response_model=CaseAuditResponse)
def audit_reference_cases(db: Session = Depends(get_db)):
    """Run a full quality audit on the reference case library.

    Returns completeness stats, missing-field breakdowns, possible
    duplicates, and actionable recommendations.  No API keys are used.
    """
    from app.services.case_quality import audit_cases as _audit
    return _audit(db)


@app.get("/reference-cases/{case_id}", response_model=ReferenceCaseResponse)
def get_reference_case(
    case_id: int,
    db: Session = Depends(get_db),
) -> ReferenceCaseResponse:
    """Get a single reference case by ID."""
    case = reference_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Reference case not found.")
    return _ref_response(case, db)


@app.post("/reference-cases/{case_id}/describe", response_model=ReferenceCaseResponse)
def describe_reference_case(
    case_id: int,
    vision: VisionAdapter = Depends(get_vision_adapter),
    db: Session = Depends(get_db),
) -> ReferenceCaseResponse:
    """Auto-generate a description for a reference case that has an image."""
    case = reference_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Reference case not found.")
    if case.image_id is None:
        raise HTTPException(status_code=400, detail="Reference case has no image attached.")

    uploaded = session_service.get_image_by_id(db, case.image_id)
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Linked image not found.")

    try:
        desc = vision.describe_image_structured(uploaded.file_path)
    except Exception as exc:
        raise _vision_http_exception(exc) from exc

    reference_service.update_case(
        db,
        case_id,
        ai_description=desc.suggested_prompt_text,
        image_description=desc.suggested_prompt_text,
    )
    case = reference_service.get_case(db, case_id)
    return _ref_response(case, db)


@app.delete("/reference-cases/{case_id}", status_code=204)
def delete_reference_case(
    case_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a reference case (does not delete the linked uploaded image)."""
    deleted = reference_service.delete_case(db, case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reference case not found.")


# ── V1.8: Semantic search over reference cases ───────────────────────────

@app.post("/reference-cases/reindex-embeddings")
def reindex_embeddings(db: Session = Depends(get_db)):
    """Generate or update embeddings for all reference cases.

    Uses the configured embedding provider (currently OpenAI text-embedding-3-small).
    Skips cases whose content hasn't changed since last index.
    """
    from app.services.embeddings import reindex_all_cases
    return reindex_all_cases(db)


@app.post("/reference-cases/search-semantic")
def search_semantic(body: dict, db: Session = Depends(get_db)):
    """Search reference cases by semantic similarity.

    Request body:
        query: str — natural language search query
        top_k: int (default 10) — number of results
        filters: {category?, aesthetic_level?, price_band?} (all optional)

    V1.9: Results include completeness_score and is_training_ready.
    Training-ready cases are sorted first, then by similarity.
    """
    query = body.get("query", "")
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    top_k = min(int(body.get("top_k", 10)), 50)
    filters = body.get("filters") or {}

    from app.services.embeddings import search_semantic as _search
    result = _search(db, query=query.strip(), top_k=top_k, filters=filters)

    # ── V1.9: Add quality fields to each result ─────────────────────
    results = result.get("results", [])
    if results:
        for r in results:
            case = reference_service.get_case(db, r["case_id"])
            if case:
                r["completeness_score"] = compute_completeness_score(case)
                r["is_training_ready"] = is_training_ready(case)
            else:
                r["completeness_score"] = 0
                r["is_training_ready"] = False
        # Sort: training-ready first, then by similarity descending
        results.sort(key=lambda r: (not r.get("is_training_ready", False), -r.get("similarity", 0)))
        result["results"] = results

    return result


@app.get("/embedding/status")
def embedding_status():
    """Return embedding provider configuration status (no key exposure)."""
    from app.services.embeddings import get_embedding_provider, is_embedding_configured, get_embedding_model
    provider = get_embedding_provider()
    return {
        "provider": provider,
        "model": get_embedding_model() if provider == "openai" else None,
        "is_configured": is_embedding_configured(),
        "message": (
            "Embedding 已配置" if is_embedding_configured()
            else "未配置 Embedding 模型。设置 EMBEDDING_PROVIDER=openai 并确保 OPENAI_API_KEY 有效即可启用语义搜索。"
        ),
    }


# ── V1.4: Compare with references ────────────────────────────────────

@app.post("/compare-with-references", response_model=CompareWithReferencesResponse)
def compare_with_references(
    body: CompareWithReferencesRequest,
    comparator: ReferenceComparatorAgent = Depends(get_reference_comparator),
    db: Session = Depends(get_db),
) -> CompareWithReferencesResponse:
    """Compare user work against curated reference cases.

    V1.8: If no case_ids are provided and semantic_query is given, uses
    semantic search to find relevant cases. Falls back to filtered list
    if semantic search is unavailable.
    """
    ref_cases = reference_service.find_cases_for_comparison(
        db,
        case_ids=body.reference_case_ids,
        category=body.category,
        style_tags=body.style_tags,
        price_band=body.price_band,
    )

    # ── V1.8: Semantic search fallback ──────────────────────────────
    if not ref_cases and body.semantic_query and not body.reference_case_ids:
        from app.services.embeddings import search_semantic as _sem_search, is_embedding_configured
        if is_embedding_configured():
            sem_result = _sem_search(
                db,
                query=body.semantic_query,
                top_k=6,
                filters={
                    "category": body.category or "",
                    "price_band": body.price_band or "",
                },
            )
            case_ids = [r["case_id"] for r in sem_result.get("results", [])]
            if case_ids:
                ref_cases = reference_service.find_cases_for_comparison(
                    db, case_ids=case_ids,
                )

    ref_data = [
        {
            "id": c.id, "title": c.title,
            "aesthetic_level": c.aesthetic_level, "category": c.category,
            "style_tags": c.style_tags, "price_band": c.price_band,
            "target_audience": c.target_audience,
            "image_description": c.image_description or c.ai_description,
            "premium_sources": c.premium_sources,
            "cheapness_sources": c.cheapness_sources,
            "learn_from_this": c.learn_from_this,
            "avoid_copying": c.avoid_copying,
            "notes": c.notes, "score": c.score,
        }
        for c in ref_cases
    ]

    return _run_agent(
        "Reference comparison",
        lambda: comparator.run(
            user_work_description=body.user_work_description,
            reference_cases=ref_data,
            image_description=body.image_description,
            user_judgment=body.user_judgment.model_dump() if body.user_judgment else None,
        ),
    )


# ── V1.4.1: Generate prompt ──────────────────────────────────────────

@app.post("/generate-prompt", response_model=GeneratedPrompt)
def generate_prompt(
    body: GeneratePromptRequest,
    generator: PromptGeneratorAgent = Depends(get_prompt_generator),
    db: Session = Depends(get_db),
) -> GeneratedPrompt:
    """Generate copyable prompts for image generation tools.

    Accepts analysis results (critique, iterate, reference comparison)
    and produces Chinese + English prompts, negative prompts, design
    notes, and usage tips.

    V1.7.2: When selected_direction is provided, the prompt is tightly
    focused on that direction. The selected_direction and generated
    prompt result are saved to the matching iterate session when possible.
    """

    def _to_dict(v: Any) -> dict | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {"raw": v}
        return None

    def _to_json_text(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False, indent=2)
        return str(v)

    selected_direction_text = _to_json_text(body.selected_direction)

    result = _run_agent(
        "Prompt generation",
        lambda: generator.run(
            work_description=body.work_description,
            image_description=body.image_description,
            user_judgment=body.user_judgment.model_dump() if body.user_judgment else None,
            critique_result=_to_dict(body.critique_result),
            iterate_result=_to_dict(body.iterate_result),
            selected_direction=selected_direction_text,
            reference_comparison=_to_dict(body.reference_comparison),
            target_tool=body.target_tool or "general",
        ),
    )

    # V1.7.2: save selected_direction + prompt_result to the iterate
    # session that produced those directions. Older clients without a
    # session_id fall back to the latest iterate record only.
    if selected_direction_text:
        try:
            record = None
            if body.session_id is not None:
                record = session_service.get_session_by_id(db, body.session_id)
                if record is None:
                    raise HTTPException(status_code=404, detail="未找到要保存提示词的训练记录。")
                if record.record_type != "iterate":
                    raise HTTPException(status_code=400, detail="只能为迭代记录保存方向提示词。")
            else:
                latest = session_service.get_recent_records(db, limit=1, record_type="iterate")
                record = latest[0] if latest else None

            if record is not None:
                record.selected_direction = selected_direction_text
                record.prompt_result = result.model_dump()
                db.commit()
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="提示词生成成功，但保存到历史记录失败。",
            ) from exc

    return result


# ── V1.5: Training workbench ──────────────────────────────────────────

@app.get("/training/today", response_model=TodayTrainingResponse)
def training_today(
    db: Session = Depends(get_db),
) -> TodayTrainingResponse:
    """Return today's training theme and tasks (rotates by date)."""
    from datetime import date as dt_date

    themes = TRAINING_THEMES
    day_index = dt_date.today().toordinal() % len(themes)
    theme = themes[day_index]

    tasks = [
        f"上传一个作品并先围绕「{theme}」自评",
        f"指出你认为最影响「{theme}」的问题",
        "和一个 high 案例对比",
        "生成修改提示词",
        "记录今天学到的一条审美规则",
    ]

    return TodayTrainingResponse(theme=theme, tasks=tasks)


@app.post("/training/sessions/{session_id}/complete", response_model=dict)
def complete_training(
    session_id: int,
    body: CompleteTrainingRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Mark a training session as complete with user notes."""
    record = session_service.get_session_by_id(db, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if body.training_theme:
        record.training_theme = body.training_theme
    if body.user_lesson:
        record.user_lesson = body.user_lesson
    if body.next_focus:
        record.next_focus = body.next_focus
    if body.after_score is not None:
        record.after_score = body.after_score
    record.completed = 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save training completion.")
    return {"status": "ok", "session_id": session_id}


@app.get("/training/stats", response_model=TrainingStatsResponse)
def training_stats(
    db: Session = Depends(get_db),
) -> TrainingStatsResponse:
    """Return training statistics."""
    from datetime import date as dt_date, timedelta

    total = session_service.get_record_count(db)
    all_records = session_service.get_recent_records(db, limit=1000)

    completed = sum(1 for r in all_records if r.completed == 1)
    today = dt_date.today()
    week_ago = today - timedelta(days=7)
    sessions_this_week = sum(
        1 for r in all_records if r.created_at and r.created_at.date() >= week_ago
    )

    # Simple streak: count consecutive days with at least one session
    streak = 0
    for i in range(30):
        d = today - timedelta(days=i)
        has_session = any(
            r.created_at and r.created_at.date() == d for r in all_records
        )
        if has_session:
            streak += 1
        else:
            break

    user_scores = [r.user_score for r in all_records if r.user_score is not None]
    ai_scores = [r.ai_score for r in all_records if r.ai_score is not None]
    gaps = [
        abs((r.user_score or 0) - (r.ai_score or 0))
        for r in all_records
        if r.user_score is not None and r.ai_score is not None
    ]

    import json as _json
    tags: list[str] = []
    for r in all_records:
        if r.training_focus_tags:
            try:
                parsed = _json.loads(r.training_focus_tags)
                if isinstance(parsed, list):
                    tags.extend(parsed)
            except Exception:
                pass

    # Most common tags (top 5)
    from collections import Counter
    common_tags = [tag for tag, _ in Counter(tags).most_common(5)]

    return TrainingStatsResponse(
        total_sessions=total,
        completed_sessions=completed,
        sessions_this_week=sessions_this_week,
        current_streak_days=streak,
        average_user_score=round(sum(user_scores) / len(user_scores), 1) if user_scores else None,
        average_ai_score=round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else None,
        average_score_gap=round(sum(gaps) / len(gaps), 1) if gaps else None,
        common_training_focus_tags=common_tags,
    )


@app.get("/training/weekly-review", response_model=WeeklyReviewResponse)
def weekly_review(
    reviewer: WeeklyReviewAgent = Depends(get_weekly_reviewer),
    db: Session = Depends(get_db),
) -> WeeklyReviewResponse:
    """Generate a weekly training review from the last 7 days."""
    from datetime import date as dt_date, timedelta

    all_records = session_service.get_recent_records(db, limit=200)
    week_ago = dt_date.today() - timedelta(days=7)
    week_records = [
        r for r in all_records
        if r.created_at and r.created_at.date() >= week_ago
    ]

    history = [
        {
            "id": r.id,
            "type": r.record_type,
            "work_description": r.work_description,
            "user_score": r.user_score,
            "ai_score": r.ai_score,
            "judgment_gap_summary": r.judgment_gap_summary,
            "training_theme": r.training_theme,
            "user_lesson": r.user_lesson,
            "completed": r.completed,
        }
        for r in week_records
    ]

    return _run_agent(
        "Weekly review",
        lambda: reviewer.run(history),
    )


# ── V2.0: Training effectiveness assessment ────────────────────────────

@app.get("/assessment/overview", response_model=AssessmentOverview)
def assessment_overview(db: Session = Depends(get_db)):
    """Return training effectiveness overview statistics.

    Includes training frequency, score gaps, gap trend, and
    a Chinese summary with suggested next steps.
    """
    from app.services.assessment import compute_overview
    return compute_overview(db)


@app.get("/assessment/mistakes", response_model=list[MistakePattern])
def assessment_mistakes(db: Session = Depends(get_db)):
    """Return common mistake patterns detected from training history.

    Uses keyword-based rule matching across judgment_gap_summary,
    training_focus_tags, user_weaknesses, and ai_main_problems.
    """
    from app.services.assessment import compute_mistake_patterns
    return compute_mistake_patterns(db)


@app.get("/assessment/dimensions", response_model=list[DimensionAssessment])
def assessment_dimensions(db: Session = Depends(get_db)):
    """Return aesthetic judgment dimension scores (0-100) and trends.

    Evaluates 7 dimensions: typography, color, composition, texture/material,
    price-band, commercial-fit, and iteration.
    """
    from app.services.assessment import compute_dimension_scores
    return compute_dimension_scores(db)


@app.get("/assessment/report", response_model=AssessmentReport)
def assessment_report(
    days: int = Query(default=7, ge=1, le=90, description="Review period in days"),
    db: Session = Depends(get_db),
):
    """Return a period review report with progress summary,
    weakest dimensions, training plan, and recommended themes.
    """
    from app.services.assessment import compute_report
    return compute_report(db, days=days)


# ── V1.8: Data export / import ──────────────────────────────────────────

@app.get("/export")
def export_data(db: Session = Depends(get_db)):
    """Export all training data as a zip backup.

    Includes: manifest, reference cases, sessions, prompts, image metadata,
    config summary (no API keys), and uploaded image files.

    Returns a zip file download.
    """
    from fastapi.responses import Response

    from app.services.data_io import export_data as _export

    try:
        zip_bytes = _export(db, _UPLOAD_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=aesthetic-backup.zip",
        },
    )


@app.post("/import")
async def import_data(
    file: UploadFile = File(description="Exported zip backup"),
    db: Session = Depends(get_db),
):
    """Import data from a V1.8 export zip.  Merge-only — never overwrites.

    Accepts a zip file upload via multipart/form-data with field name ``file``.
    Validates zip structure, prevents path traversal, remaps image/case IDs,
    and returns import statistics.
    """
    from app.services.data_io import import_data as _import

    try:
        zip_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="无法读取上传文件")
    try:
        result = _import(db, zip_bytes, _UPLOAD_DIR)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import zipfile as _zipfile
        if isinstance(e, _zipfile.BadZipFile):
            raise HTTPException(status_code=400, detail="无效的 zip 文件格式")
        raise HTTPException(status_code=500, detail="导入失败，请检查备份包内容后重试。")
    return result.to_dict()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "backend", "version": "v2.0.0"}


@app.get("/model/status")
def model_status() -> dict:
    """Return DeepSeek config status without exposing the API key."""
    key = get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY").strip()
    placeholder_keys = {"", "replace-me", "your_deepseek_api_key_here", "replace-with-your-key"}
    is_configured = bool(key) and key not in placeholder_keys
    return {
        "provider": "deepseek",
        "is_configured": is_configured,
        "missing_keys": [] if is_configured else ["DEEPSEEK_API_KEY"],
        "default_model": get_value("deepseek", "default_model", env_var="DEEPSEEK_DEFAULT_MODEL") or "deepseek-v4-flash",
        "reasoning_model": get_value("deepseek", "reasoning_model", env_var="DEEPSEEK_REASONING_MODEL") or "deepseek-v4-pro",
    }


# ── V1.7.1: System status (combined health/model/vision/db/uploads) ─────

@app.get("/system/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    """Return a consolidated status snapshot for the config status bar.

    Combines backend health, model config, vision config, database
    connectivity, and upload directory writability.  No API keys are
    exposed — only boolean ``configured`` flags are returned.
    """
    from sqlalchemy import text

    # ── DeepSeek ───────────────────────────────────────────────────
    key = get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY").strip()
    placeholder_keys = {
        "", "replace-me", "your_deepseek_api_key_here", "replace-with-your-key",
    }
    deepseek_configured = bool(key) and key not in placeholder_keys

    # ── Vision ─────────────────────────────────────────────────────
    provider = get_vision_provider()
    vision_configured = is_vision_configured(provider)
    is_placeholder_vision = provider == "placeholder"

    # ── Database ───────────────────────────────────────────────────
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "error"

    # ── Uploads ────────────────────────────────────────────────────
    uploads_ok = _UPLOAD_DIR.exists() and os.access(str(_UPLOAD_DIR), os.W_OK)

    # ── Setup ──────────────────────────────────────────────────────
    setup_completed = (
        get_value("setup", "completed", default="") == "true"
    )

    # ── Embedding ──────────────────────────────────────────────────
    from app.services.embeddings import is_embedding_configured as _emb_ok
    embedding_configured = _emb_ok()

    return {
        "backend": "ok",
        "version": "v2.0.0",
        "deepseek": {"configured": deepseek_configured},
        "vision": {
            "configured": vision_configured,
            "provider": provider,
            "is_placeholder": is_placeholder_vision,
        },
        "embedding": {"configured": embedding_configured},
        "database": database_status,
        "uploads": "ok" if uploads_ok else "error",
        "setup_completed": setup_completed,
    }


# ── V1.7.1: Setup wizard state ──────────────────────────────────────────

@app.get("/setup/status")
def setup_status() -> dict:
    """Return whether the setup wizard has been completed."""
    completed = get_value("setup", "completed", default="") == "true"
    return {"setup_completed": completed}


@app.post("/setup/complete")
def setup_complete() -> dict:
    """Mark the setup wizard as completed."""
    from app.settings.config_store import write_config as _write
    config = get_config()
    if "setup" not in config:
        config["setup"] = {}
    config["setup"]["completed"] = "true"
    _write(config)
    return {"status": "ok", "setup_completed": True}


