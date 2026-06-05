"""Reference case service — CRUD for the V1.4 reference case library."""

from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import ReferenceCase


def create_case(db: Session, **kwargs: Any) -> ReferenceCase:
    """Create a new reference case."""
    case = ReferenceCase(**kwargs)
    db.add(case)
    try:
        db.commit()
        db.refresh(case)
    except SQLAlchemyError:
        db.rollback()
        raise
    return case


def list_cases(
    db: Session,
    *,
    category: str | None = None,
    aesthetic_level: str | None = None,
    style_tag: str | None = None,
    price_band: str | None = None,
    limit: int = 50,
) -> list[ReferenceCase]:
    """List reference cases with optional filters."""
    query = db.query(ReferenceCase).order_by(ReferenceCase.created_at.desc())
    if category:
        query = query.filter(ReferenceCase.category == category)
    if aesthetic_level:
        query = query.filter(ReferenceCase.aesthetic_level == aesthetic_level)
    if style_tag:
        query = query.filter(ReferenceCase.style_tags.contains(style_tag))
    if price_band:
        query = query.filter(ReferenceCase.price_band == price_band)
    return query.limit(limit).all()


def get_case(db: Session, case_id: int) -> ReferenceCase | None:
    """Return a single reference case by ID."""
    return db.query(ReferenceCase).filter(ReferenceCase.id == case_id).first()


def update_case(db: Session, case_id: int, **kwargs: Any) -> ReferenceCase | None:
    """Update a reference case."""
    case = db.query(ReferenceCase).filter(ReferenceCase.id == case_id).first()
    if case is None:
        return None
    for key, value in kwargs.items():
        if hasattr(case, key):
            setattr(case, key, value)
    try:
        db.commit()
        db.refresh(case)
    except SQLAlchemyError:
        db.rollback()
        raise
    return case


def delete_case(db: Session, case_id: int) -> bool:
    """Delete a reference case. Returns True if deleted, False if not found."""
    case = db.query(ReferenceCase).filter(ReferenceCase.id == case_id).first()
    if case is None:
        return False
    db.delete(case)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return True


def find_cases_for_comparison(
    db: Session,
    *,
    case_ids: list[int] | None = None,
    category: str | None = None,
    style_tags: list[str] | None = None,
    price_band: str | None = None,
    max_results: int = 6,
) -> list[ReferenceCase]:
    """Find reference cases for comparison.

    If case_ids is provided, return those specific cases.
    Otherwise, search by category / style_tags / price_band,
    preferring a mix of high/medium/low levels.
    """
    if case_ids:
        return (
            db.query(ReferenceCase)
            .filter(ReferenceCase.id.in_(case_ids))
            .limit(max_results)
            .all()
        )

    query = db.query(ReferenceCase)
    if category:
        query = query.filter(ReferenceCase.category == category)
    if price_band:
        query = query.filter(ReferenceCase.price_band == price_band)
    if style_tags:
        for tag in style_tags:
            query = query.filter(ReferenceCase.style_tags.contains(tag))

    cases = query.order_by(ReferenceCase.created_at.desc()).limit(max_results * 3).all()

    # Try for a balanced mix of levels
    high = [c for c in cases if c.aesthetic_level == "high"]
    medium = [c for c in cases if c.aesthetic_level == "medium"]
    low = [c for c in cases if c.aesthetic_level == "low"]
    other = [c for c in cases if c.aesthetic_level not in ("high", "medium", "low")]

    result: list[ReferenceCase] = []
    for i in range(max(2, max_results // 3)):
        if high and len(result) < max_results:
            result.append(high.pop(0))
        if medium and len(result) < max_results:
            result.append(medium.pop(0))
        if low and len(result) < max_results:
            result.append(low.pop(0))
    result.extend(other[: max_results - len(result)])
    result.extend(high[: max_results - len(result)])
    result.extend(medium[: max_results - len(result)])

    return result[:max_results]
