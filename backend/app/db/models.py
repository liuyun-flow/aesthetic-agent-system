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

    # ── V1.5: Training workbench ────────────────────────────────────
    training_theme = Column(String(100), nullable=True)
    user_lesson = Column(Text, nullable=True)
    next_focus = Column(Text, nullable=True)
    completed = Column(Integer, nullable=True, default=0)  # 0/1 boolean
    before_score = Column(Integer, nullable=True)
    after_score = Column(Integer, nullable=True)

    # ── V1.7.2: Iteration direction selection + generated prompt ─────
    selected_direction = Column(Text, nullable=True)
    prompt_result = Column(JSON, nullable=True)

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


class ReferenceCase(Base):
    """V1.4: Curated reference cases for aesthetic comparison training."""

    __tablename__ = "reference_cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    category = Column(String(100), nullable=True)
    aesthetic_level = Column(String(20), nullable=True, default="unknown")  # high / medium / low / unknown
    style_tags = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    price_band = Column(String(100), nullable=True)
    image_id = Column(Integer, nullable=True)
    image_description = Column(Text, nullable=True)
    ai_description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # 0-100
    # V1.5.1: Enhanced aesthetic annotations
    premium_sources = Column(Text, nullable=True)
    cheapness_sources = Column(Text, nullable=True)
    learn_from_this = Column(Text, nullable=True)
    avoid_copying = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ReferenceCase id={self.id} title={self.title} level={self.aesthetic_level}>"


class ReferenceCaseEmbedding(Base):
    """V1.8: Pre-computed embeddings for semantic search over reference cases."""

    __tablename__ = "reference_case_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    reference_case_id = Column(Integer, nullable=False, index=True)
    embedding_provider = Column(String(50), nullable=False)
    embedding_model = Column(String(100), nullable=False)
    embedding_json = Column(Text, nullable=False)  # JSON-serialized float list
    source_text_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
