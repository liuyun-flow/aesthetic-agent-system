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

    def __repr__(self) -> str:
        return (
            f"<TrainingRecord id={self.id} type={self.record_type} "
            f"created_at={self.created_at}>"
        )
