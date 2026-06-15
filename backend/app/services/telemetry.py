"""V2.5: lightweight LLM telemetry — record token usage + latency per call.

Writes are best-effort and must NEVER break a real request (all failures
swallowed). Recording opens its own short-lived session so it is independent
of the request's DB session.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import LlmUsage


def record_usage(provider: str | None, model: str | None, usage: Any, latency_ms: float) -> None:
    """Persist one LLM call's tokens + latency. Best-effort, never raises."""
    prompt = completion = total = None
    if usage is not None:
        prompt = getattr(usage, "prompt_tokens", None)
        completion = getattr(usage, "completion_tokens", None)
        total = getattr(usage, "total_tokens", None)

    try:
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            db.add(
                LlmUsage(
                    provider=provider or "",
                    model=model or "",
                    prompt_tokens=prompt,
                    completion_tokens=completion,
                    total_tokens=total,
                    latency_ms=int(round(latency_ms)),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass  # telemetry must never break the request


def get_usage_summary(db: Session) -> dict[str, Any]:
    """Aggregate all recorded LLM usage into totals + a per-model breakdown."""
    rows = db.query(LlmUsage).all()
    total_calls = len(rows)
    total_tokens = sum(r.total_tokens or 0 for r in rows)
    total_prompt = sum(r.prompt_tokens or 0 for r in rows)
    total_completion = sum(r.completion_tokens or 0 for r in rows)
    avg_latency = (
        round(sum(r.latency_ms or 0 for r in rows) / total_calls, 1)
        if total_calls
        else None
    )

    by_model: dict[str, dict[str, int]] = {}
    for r in rows:
        key = r.model or "?"
        entry = by_model.setdefault(key, {"calls": 0, "total_tokens": 0})
        entry["calls"] += 1
        entry["total_tokens"] += r.total_tokens or 0

    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "avg_latency_ms": avg_latency,
        "by_model": [
            {"model": k, "calls": v["calls"], "total_tokens": v["total_tokens"]}
            for k, v in sorted(by_model.items(), key=lambda kv: -kv[1]["total_tokens"])
        ],
    }
