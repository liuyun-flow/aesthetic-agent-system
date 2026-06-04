"""Pydantic response schemas for all endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── /analyze ──────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    color: str = Field(..., description="Color scheme analysis")
    composition: str = Field(..., description="Composition analysis")
    typography: str = Field(..., description="Typography / font analysis")
    material: str = Field(..., description="Material / texture feel analysis")
    emotion: str = Field(..., description="Emotional impact analysis")
    brand_sense: str = Field(..., description="Brand perception analysis")
    premium_sources: str = Field(..., description="Sources of premium feel")
    cheapness_sources: str = Field(..., description="Sources of cheapness")
    improvement_suggestions: str = Field(..., description="Actionable improvement ideas")


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
    main_issues: list[str] = Field(default_factory=list)
    cheapness_sources: list[str] = Field(default_factory=list)
    priority_fixes: list[str] = Field(default_factory=list)


# ── /iterate ──────────────────────────────────────────────────────────

class IterationDirection(BaseModel):
    title: str
    description: str
    expected_impact: str


class IterateResponse(BaseModel):
    directions: list[IterationDirection] = Field(..., min_length=1, max_length=5)


# ── /profile ──────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    preferences: str = Field(..., description="Summarized design preferences")
    common_mistakes: str = Field(..., description="Frequently observed mistakes")
    next_week_focus: str = Field(..., description="Recommended focus areas for next week")
    total_sessions: int = Field(..., description="Total number of training records")


# ── /sessions ─────────────────────────────────────────────────────────

class SessionRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    record_type: str
    work_description: str
    created_at: datetime


class SessionsResponse(BaseModel):
    sessions: list[SessionRecord]
    total: int
