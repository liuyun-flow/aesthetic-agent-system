"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.db.database import Base


class TrainingRecord(Base):
    """Stores every analyze / critique / iterate call as a training record."""

    __tablename__ = "training_records"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(
        String(20), nullable=False, index=True
    )  # "analyze" | "critique" | "iterate"
    work_description = Column(Text, nullable=False)
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── V1.1: User self-assessment ──────────────────────────────────
    user_score = Column(Integer, nullable=True)
    user_strengths = Column(Text, nullable=True)
    user_weaknesses = Column(Text, nullable=True)
    user_priority_fixes = Column(Text, nullable=True)
    user_target_audience = Column(Text, nullable=True)
    user_price_band = Column(Text, nullable=True)

    # ── V1.1: AI scoring summary ────────────────────────────────────
    ai_score = Column(Integer, nullable=True)
    ai_main_problems = Column(Text, nullable=True)
    ai_priority_fixes = Column(Text, nullable=True)

    # ── V1.1: Judgment gap ──────────────────────────────────────────
    judgment_gap_summary = Column(Text, nullable=True)
    training_focus_tags = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TrainingRecord id={self.id} type={self.record_type} "
            f"created_at={self.created_at}>"
        )


class UploadedImage(Base):
    """Stores metadata for every uploaded image."""

    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(512), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # V1.3: AI-generated description
    ai_description = Column(Text, nullable=True)
    vision_provider = Column(String(50), nullable=True)
    vision_description_json = Column(Text, nullable=True)
    described_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UploadedImage id={self.id} filename={self.stored_filename}>"
