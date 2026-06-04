"""Session service — persists and retrieves training records."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models import TrainingRecord


def save_record(
    db: Session,
    record_type: str,
    work_description: str,
    result: Any,
) -> TrainingRecord:
    """Persist a training record (analyze / critique / iterate)."""
    # Convert Pydantic model to dict for JSON storage
    if hasattr(result, "model_dump"):
        result_json = result.model_dump()
    elif hasattr(result, "dict"):
        result_json = result.dict()
    else:
        result_json = result

    record = TrainingRecord(
        record_type=record_type,
        work_description=work_description,
        result_json=result_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recent_records(
    db: Session,
    limit: int = 50,
    record_type: Optional[str] = None,
) -> list[TrainingRecord]:
    """Return the most recent training records, optionally filtered by type."""
    query = db.query(TrainingRecord).order_by(TrainingRecord.created_at.desc())
    if record_type:
        query = query.filter(TrainingRecord.record_type == record_type)
    return query.limit(limit).all()


def get_record_count(db: Session, record_type: Optional[str] = None) -> int:
    """Count records, optionally filtered by type."""
    query = db.query(TrainingRecord)
    if record_type:
        query = query.filter(TrainingRecord.record_type == record_type)
    return query.count()


def get_history_for_profile(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent records as dicts suitable for profile analysis."""
    records = get_recent_records(db, limit=limit)
    return [
        {
            "id": r.id,
            "type": r.record_type,
            "work_description": r.work_description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
