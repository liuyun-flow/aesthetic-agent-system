"""Session service — persists and retrieves training records and uploaded images."""

from datetime import date
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import TrainingRecord, UploadedImage

VALID_RECORD_TYPES = {"analyze", "critique", "iterate"}


def save_record(
    db: Session,
    record_type: str,
    work_description: str,
    result: Any,
    *,
    user_judgment: dict[str, Any] | None = None,
    user_score: int | None = None,
    user_strengths: str | None = None,
    user_weaknesses: str | None = None,
    user_priority_fixes: str | None = None,
    user_target_audience: str | None = None,
    user_price_band: str | None = None,
    ai_score: int | None = None,
    ai_main_problems: str | None = None,
    ai_priority_fixes: str | None = None,
    judgment_gap_summary: str | None = None,
    training_focus_tags: str | None = None,
    selected_direction: str | None = None,
    prompt_result: dict[str, Any] | None = None,
) -> TrainingRecord:
    """Persist a training record (analyze / critique / iterate).

    V1.1: Accepts optional user judgment and AI comparison fields
    for the training-loop feature.
    V1.7.2: Accepts selected_direction and prompt_result for
    iteration direction selection + prompt generation persistence.
    """
    if record_type not in VALID_RECORD_TYPES:
        raise ValueError(f"Unsupported record type: {record_type}")

    result_json = jsonable_encoder(result)

    record = TrainingRecord(
        record_type=record_type,
        work_description=work_description,
        result_json=result_json,
        user_score=user_score,
        user_strengths=user_strengths,
        user_weaknesses=user_weaknesses,
        user_priority_fixes=user_priority_fixes,
        user_target_audience=user_target_audience,
        user_price_band=user_price_band,
        ai_score=ai_score,
        ai_main_problems=ai_main_problems,
        ai_priority_fixes=ai_priority_fixes,
        judgment_gap_summary=judgment_gap_summary,
        training_focus_tags=training_focus_tags,
        selected_direction=selected_direction,
        prompt_result=prompt_result,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except SQLAlchemyError:
        db.rollback()
        raise
    return record


def get_session_by_id(db: Session, session_id: int) -> TrainingRecord | None:
    """Return a single training record by ID, or None."""
    return db.query(TrainingRecord).filter(TrainingRecord.id == session_id).first()


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


def get_all_records(
    db: Session,
    limit: int = 2000,
) -> list[TrainingRecord]:
    """Return all training records (most recent first), without type filter.

    V2.0: Used by assessment service for full historical analysis.
    """
    return (
        db.query(TrainingRecord)
        .order_by(TrainingRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_records_in_range(
    db: Session,
    start_date: date,
    end_date: date,
    limit: int = 2000,
) -> list[TrainingRecord]:
    """Return training records whose created_at falls in [start_date, end_date].

    V2.0: Used by assessment service for period-based analysis.
    """
    return (
        db.query(TrainingRecord)
        .filter(TrainingRecord.created_at >= start_date)
        .filter(TrainingRecord.created_at <= end_date)
        .order_by(TrainingRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_history_for_profile(db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent records as dicts suitable for profile analysis.

    V1.1: Includes judgment gap fields so the profile agent can analyze
    user blind spots and training needs.
    """
    records = get_recent_records(db, limit=limit)
    return [
        {
            "id": r.id,
            "type": r.record_type,
            "work_description": r.work_description,
            "result": r.result_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            # V1.1 judgment fields
            "user_score": r.user_score,
            "user_strengths": r.user_strengths,
            "user_weaknesses": r.user_weaknesses,
            "user_priority_fixes": r.user_priority_fixes,
            "user_target_audience": r.user_target_audience,
            "user_price_band": r.user_price_band,
            "ai_score": r.ai_score,
            "ai_main_problems": r.ai_main_problems,
            "ai_priority_fixes": r.ai_priority_fixes,
            "judgment_gap_summary": r.judgment_gap_summary,
            "training_focus_tags": r.training_focus_tags,
        }
        for r in records
    ]


# ── Image upload ─────────────────────────────────────────────────────

def save_image(
    db: Session,
    *,
    original_filename: str,
    stored_filename: str,
    file_path: str,
    content_type: str,
    size_bytes: int,
) -> UploadedImage:
    """Persist uploaded image metadata (V1.2 expanded schema)."""
    image = UploadedImage(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    db.add(image)
    try:
        db.commit()
        db.refresh(image)
    except SQLAlchemyError:
        db.rollback()
        raise
    return image


def get_image_by_id(db: Session, image_id: int) -> UploadedImage | None:
    """Return an uploaded image by primary key, or None."""
    return db.query(UploadedImage).filter(UploadedImage.id == image_id).first()


def update_image_description(
    db: Session,
    image_id: int,
    *,
    ai_description: str | None = None,
    vision_provider: str | None = None,
    vision_description_json: str | None = None,
) -> UploadedImage | None:
    """Update an image record with AI-generated description (V1.3)."""
    from datetime import datetime as dt

    image = db.query(UploadedImage).filter(UploadedImage.id == image_id).first()
    if image is None:
        return None
    image.ai_description = ai_description
    image.vision_provider = vision_provider
    image.vision_description_json = vision_description_json
    image.described_at = dt.utcnow()
    try:
        db.commit()
        db.refresh(image)
    except SQLAlchemyError:
        db.rollback()
        raise
    return image
