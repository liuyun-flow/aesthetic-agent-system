"""Database engine and session management."""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database/aesthetic.db")

_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables and run safe migrations."""
    Base.metadata.create_all(bind=engine)
    _migrate_v1_1()
    _migrate_v1_2()
    _migrate_v1_3()
    _migrate_v1_4()
    _migrate_v1_5()
    _migrate_v1_5_1()
    _migrate_v1_7_2()
    _migrate_v1_8()
    _migrate_v2_3()
    _migrate_v2_4()


def _migrate_v2_4() -> None:
    """V2.4: Add stored AI dimension scores to training_records.

    Additive + idempotent (safe on existing DBs). Old rows keep these NULL and
    the assessment layer falls back to the legacy keyword path for them.
    """
    v2_4_columns: list[tuple[str, str]] = [
        ("ai_dimension_scores", "JSON"),
        ("ai_overall_score", "INTEGER"),
        ("eval_prompt_version", "VARCHAR(20)"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v2_4_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE training_records ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass  # Column already exists — safe to skip
        conn.commit()


def _migrate_v2_3() -> None:
    """V2.3: Add image_id to training_records (link session → its image)."""
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql(
                "ALTER TABLE training_records ADD COLUMN image_id INTEGER"
            )
        except Exception:
            pass  # Column already exists — safe to skip
        conn.commit()


def _migrate_v1_8() -> None:
    """V1.8: Create reference_case_embeddings table."""
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[Base.metadata.tables["reference_case_embeddings"]],
        )
    except Exception:
        pass  # Table already exists


def _migrate_v1_7_2() -> None:
    """V1.7.2: Add selected_direction and prompt_result to training_records."""
    v1_7_2_columns: list[tuple[str, str]] = [
        ("selected_direction", "TEXT"),
        ("prompt_result", "JSON"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v1_7_2_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE training_records ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass
        conn.commit()


def _migrate_v1_5_1() -> None:
    """V1.5.1: Add aesthetic annotation columns to reference_cases."""
    v1_5_1_columns: list[tuple[str, str]] = [
        ("premium_sources", "TEXT"),
        ("cheapness_sources", "TEXT"),
        ("learn_from_this", "TEXT"),
        ("avoid_copying", "TEXT"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v1_5_1_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE reference_cases ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass
        conn.commit()


def _migrate_v1_5() -> None:
    """V1.5: Add training workbench columns."""
    v1_5_columns: list[tuple[str, str]] = [
        ("training_theme", "VARCHAR(100)"),
        ("user_lesson", "TEXT"),
        ("next_focus", "TEXT"),
        ("completed", "INTEGER DEFAULT 0"),
        ("before_score", "INTEGER"),
        ("after_score", "INTEGER"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v1_5_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE training_records ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass
        conn.commit()


def _migrate_v1_3() -> None:
    """V1.3: Add AI vision description columns to uploaded_images."""
    v1_3_columns: list[tuple[str, str]] = [
        ("ai_description", "TEXT"),
        ("vision_provider", "VARCHAR(50)"),
        ("vision_description_json", "TEXT"),
        ("described_at", "DATETIME"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v1_3_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE uploaded_images ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass
        conn.commit()


def _migrate_v1_4() -> None:
    """V1.4: Create reference_cases table if it doesn't exist."""
    try:
        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["reference_cases"]])
    except Exception:
        pass  # Table already exists


def _migrate_v1_2() -> None:
    """V1.2: Ensure uploaded_images table has the expanded schema."""
    v1_2_upgrades = [
        # New columns for v1.2
        ("original_filename", "VARCHAR(512)"),
        ("content_type", "VARCHAR(100)"),
        ("size_bytes", "INTEGER"),
    ]
    # Rename old columns if they exist (idempotent with try/except)
    renames = [
        ("filename", "stored_filename"),
        ("path", "file_path"),
    ]
    with engine.connect() as conn:
        for old, new in renames:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE uploaded_images RENAME COLUMN {old} TO {new}"
                )
            except Exception:
                pass
        for col_name, col_type in v1_2_upgrades:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE uploaded_images ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass
        conn.commit()


def _migrate_v1_1() -> None:
    """Add V1.1 columns to training_records if they don't exist (safe for SQLite)."""
    v1_1_columns: list[tuple[str, str]] = [
        ("user_score", "INTEGER"),
        ("user_strengths", "TEXT"),
        ("user_weaknesses", "TEXT"),
        ("user_priority_fixes", "TEXT"),
        ("user_target_audience", "TEXT"),
        ("user_price_band", "TEXT"),
        ("ai_score", "INTEGER"),
        ("ai_main_problems", "TEXT"),
        ("ai_priority_fixes", "TEXT"),
        ("judgment_gap_summary", "TEXT"),
        ("training_focus_tags", "TEXT"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in v1_1_columns:
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE training_records ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass  # Column already exists — safe to skip
        conn.commit()
