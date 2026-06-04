"""Pydantic response schemas for all endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RecordType = Literal["analyze", "critique", "iterate"]


# ── /analyze ──────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    color: str = Field(..., min_length=1, description="Color scheme analysis")
    composition: str = Field(..., min_length=1, description="Composition analysis")
    typography: str = Field(..., min_length=1, description="Typography / font analysis")
    material: str = Field(..., min_length=1, description="Material / texture feel analysis")
    emotion: str = Field(..., min_length=1, description="Emotional impact analysis")
    brand_sense: str = Field(..., min_length=1, description="Brand perception analysis")
    premium_sources: str = Field(..., min_length=1, description="Sources of premium feel")
    cheapness_sources: str = Field(..., min_length=1, description="Sources of cheapness")
    improvement_suggestions: str = Field(
        ..., min_length=1, description="Actionable improvement ideas"
    )


# ── /critique ─────────────────────────────────────────────────────────

class DimensionScores(BaseModel):
    color: float = Field(..., ge=1, le=10)
    composition: float = Field(..., ge=1, le=10)
    typography: float = Field(..., ge=1, le=10)
    material: float = Field(..., ge=1, le=10)
    emotion: float = Field(..., ge=1, le=10)
    brand_sense: float = Field(..., ge=1, le=10)


class CritiqueResponse(BaseModel):
    total_score: float = Field(..., ge=1, le=10, description="Weighted total score 1-10")
    dimensions: DimensionScores
    main_issues: list[str] = Field(..., min_length=1, max_length=10)
    cheapness_sources: list[str] = Field(..., max_length=10)
    priority_fixes: list[str] = Field(..., min_length=1, max_length=10)


# ── /iterate ──────────────────────────────────────────────────────────

class IterationDirection(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    expected_impact: str = Field(..., min_length=1)


class IterateResponse(BaseModel):
    directions: list[IterationDirection] = Field(..., min_length=1, max_length=5)


# ── /profile ──────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    preferences: str = Field(..., min_length=1, description="Summarized design preferences")
    common_mistakes: str = Field(..., min_length=1, description="Frequently observed mistakes")
    next_week_focus: str = Field(
        ..., min_length=1, description="Recommended focus areas for next week"
    )
    total_sessions: int = Field(..., ge=0, description="Total number of training records")


# ── /sessions ─────────────────────────────────────────────────────────

class SessionRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    record_type: RecordType
    work_description: str
    created_at: datetime


class SessionsResponse(BaseModel):
    sessions: list[SessionRecord]
    total: int = Field(..., ge=0)
