"""FastAPI application — aesthetic training agent system MVP."""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Callable, TypeVar

from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.analyzer import AnalyzerAgent
from app.agents.comparator import ComparatorAgent
from app.agents.critic import CriticAgent
from app.agents.iterator import IteratorAgent
from app.agents.profile import ProfileAgent
from app.agents.reference_comparator import ReferenceComparatorAgent
from app.db.database import get_db, init_db
from app.llm.deepseek_client import (
    get_deepseek_client,
    get_default_model,
    get_reasoning_model,
)
from app.schemas.requests import (
    CompareWithReferencesRequest,
    ReferenceCaseCreate,
    WorkDescriptionRequest,
)
from app.schemas.responses import (
    AnalyzeResponse,
    CompareWithReferencesResponse,
    CritiqueResponse,
    ImageDescribeResponse,
    IterateResponse,
    JudgmentGap,
    ProfileResponse,
    RecordType,
    ReferenceCaseListResponse,
    ReferenceCaseResponse,
    SessionRecord,
    SessionsResponse,
    UploadResponse,
    VisionDescription,
)
from app.services import session_service, reference_service
from app.vision.base import VisionAdapter
from app.vision.manual_adapter import ManualAdapter
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
    version="0.1.0",
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
_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")


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
    - ``placeholder`` (V1.3 default) — mock structured descriptions
    - ``manual`` — user provides image_description (V1.2 compat)
    - ``openai`` — (future) OpenAI Vision
    - ``claude`` — (future) Claude Vision
    """
    provider = os.getenv("VISION_PROVIDER", "placeholder").strip().lower()
    if provider == "manual":
        return ManualAdapter()
    # Default to placeholder (also catches "placeholder" explicitly)
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
        "user_strengths": _json.dumps(uj.strengths) if uj.strengths else None,
        "user_weaknesses": _json.dumps(uj.weaknesses) if uj.weaknesses else None,
        "user_priority_fixes": _json.dumps(uj.priority_fixes) if uj.priority_fixes else None,
        "user_target_audience": uj.target_audience,
        "user_price_band": uj.price_band,
        "ai_score": ai_score,
        "ai_main_problems": ai_problems,
        "ai_priority_fixes": ai_fixes,
        "judgment_gap_summary": gap.short_summary,
        "training_focus_tags": _json.dumps(gap.next_training_focus) if gap.next_training_focus else None,
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
    try:
        return vision.describe_image(
            uploaded.file_path,
            hint=request.image_description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
        raise HTTPException(
            status_code=502,
            detail=f"Vision adapter failed: {exc}",
        ) from exc

    # Persist the description on the image record
    import json as _json
    provider = os.getenv("VISION_PROVIDER", "placeholder")
    session_service.update_image_description(
        db,
        image_id=image_id,
        ai_description=desc.suggested_prompt_text,
        vision_provider=provider,
        vision_description_json=_json.dumps(desc.model_dump(), ensure_ascii=False),
    )

    return ImageDescribeResponse(image_id=image_id, description=desc)


# ── V1.4: Reference Cases ────────────────────────────────────────────

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
        created_at=dt.utcnow(),
        updated_at=dt.utcnow(),
    )
    return ReferenceCaseResponse.model_validate(case)


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
        cases=[ReferenceCaseResponse.model_validate(c) for c in cases],
        total=len(cases),
    )


@app.get("/reference-cases/{case_id}", response_model=ReferenceCaseResponse)
def get_reference_case(
    case_id: int,
    db: Session = Depends(get_db),
) -> ReferenceCaseResponse:
    """Get a single reference case by ID."""
    case = reference_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Reference case not found.")
    return ReferenceCaseResponse.model_validate(case)


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
        raise HTTPException(status_code=502, detail=f"Vision adapter failed: {exc}")

    reference_service.update_case(
        db,
        case_id,
        ai_description=desc.suggested_prompt_text,
        image_description=desc.suggested_prompt_text,
    )
    case = reference_service.get_case(db, case_id)
    return ReferenceCaseResponse.model_validate(case)


@app.delete("/reference-cases/{case_id}", status_code=204)
def delete_reference_case(
    case_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a reference case (does not delete the linked uploaded image)."""
    deleted = reference_service.delete_case(db, case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reference case not found.")


# ── V1.4: Compare with references ────────────────────────────────────

@app.post("/compare-with-references", response_model=CompareWithReferencesResponse)
def compare_with_references(
    body: CompareWithReferencesRequest,
    comparator: ReferenceComparatorAgent = Depends(get_reference_comparator),
    db: Session = Depends(get_db),
) -> CompareWithReferencesResponse:
    """Compare user work against curated reference cases."""
    ref_cases = reference_service.find_cases_for_comparison(
        db,
        case_ids=body.reference_case_ids,
        category=body.category,
        style_tags=body.style_tags,
        price_band=body.price_band,
    )

    ref_data = [
        {
            "id": c.id,
            "title": c.title,
            "aesthetic_level": c.aesthetic_level,
            "style_tags": c.style_tags,
            "price_band": c.price_band,
            "image_description": c.image_description or c.ai_description,
            "notes": c.notes,
            "score": c.score,
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
