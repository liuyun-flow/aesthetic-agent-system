"""FastAPI application — aesthetic training agent system MVP."""

from contextlib import asynccontextmanager
from typing import Annotated, Callable, TypeVar

from fastapi import FastAPI, Depends, HTTPException, Query
from openai import OpenAIError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.analyzer import AnalyzerAgent
from app.agents.critic import CriticAgent
from app.agents.iterator import IteratorAgent
from app.agents.profile import ProfileAgent
from app.db.database import get_db, init_db
from app.llm.deepseek_client import (
    get_deepseek_client,
    get_default_model,
    get_reasoning_model,
)
from app.schemas.requests import WorkDescriptionRequest
from app.schemas.responses import (
    AnalyzeResponse,
    CritiqueResponse,
    IterateResponse,
    ProfileResponse,
    RecordType,
    SessionRecord,
    SessionsResponse,
)
from app.services import session_service

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
) -> None:
    try:
        session_service.save_record(
            db,
            record_type=record_type,
            work_description=work_description,
            result=result,
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


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: WorkDescriptionRequest,
    agent: AnalyzerAgent = Depends(get_analyzer),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Analyze a work description across 9 aesthetic dimensions."""
    result = _run_agent("LLM analysis", lambda: agent.run(request.work_description))
    _save_record(db, "analyze", request.work_description, result)
    return result


@app.post("/critique", response_model=CritiqueResponse)
def critique(
    request: WorkDescriptionRequest,
    agent: CriticAgent = Depends(get_critic),
    db: Session = Depends(get_db),
) -> CritiqueResponse:
    """Critique a work with dimension scores, issues, and priority fixes."""
    result = _run_agent("LLM critique", lambda: agent.run(request.work_description))
    _save_record(db, "critique", request.work_description, result)
    return result


@app.post("/iterate", response_model=IterateResponse)
def iterate(
    request: WorkDescriptionRequest,
    agent: IteratorAgent = Depends(get_iterator),
    db: Session = Depends(get_db),
) -> IterateResponse:
    """Generate 3-5 distinct iteration directions for a work."""
    result = _run_agent("LLM iteration", lambda: agent.run(request.work_description))
    _save_record(db, "iterate", request.work_description, result)
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
        )
        for r in records
    ]
    return SessionsResponse(sessions=session_records, total=len(session_records))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
