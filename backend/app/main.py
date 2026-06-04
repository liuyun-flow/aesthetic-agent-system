"""FastAPI application — aesthetic training agent system MVP."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
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
    SessionRecord,
    SessionsResponse,
)
from app.services import session_service


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
    return get_deepseek_client()


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


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: WorkDescriptionRequest,
    agent: AnalyzerAgent = Depends(get_analyzer),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Analyze a work description across 9 aesthetic dimensions."""
    try:
        result = agent.run(request.work_description)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {exc}")

    session_service.save_record(
        db,
        record_type="analyze",
        work_description=request.work_description,
        result=result,
    )
    return result


@app.post("/critique", response_model=CritiqueResponse)
def critique(
    request: WorkDescriptionRequest,
    agent: CriticAgent = Depends(get_critic),
    db: Session = Depends(get_db),
) -> CritiqueResponse:
    """Critique a work with dimension scores, issues, and priority fixes."""
    try:
        result = agent.run(request.work_description)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM critique failed: {exc}")

    session_service.save_record(
        db,
        record_type="critique",
        work_description=request.work_description,
        result=result,
    )
    return result


@app.post("/iterate", response_model=IterateResponse)
def iterate(
    request: WorkDescriptionRequest,
    agent: IteratorAgent = Depends(get_iterator),
    db: Session = Depends(get_db),
) -> IterateResponse:
    """Generate 3-5 distinct iteration directions for a work."""
    try:
        result = agent.run(request.work_description)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM iteration failed: {exc}")

    session_service.save_record(
        db,
        record_type="iterate",
        work_description=request.work_description,
        result=result,
    )
    return result


@app.get("/profile", response_model=ProfileResponse)
def profile(
    agent: ProfileAgent = Depends(get_profile_agent),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    """Summarize user aesthetic profile from recent training history."""
    total = session_service.get_record_count(db)
    history = session_service.get_history_for_profile(db)

    try:
        return agent.run(history, total_sessions=total)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM profile failed: {exc}")


@app.get("/sessions", response_model=SessionsResponse)
def sessions(
    record_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> SessionsResponse:
    """Return recent training session records."""
    records = session_service.get_recent_records(
        db, limit=min(limit, 200), record_type=record_type
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
