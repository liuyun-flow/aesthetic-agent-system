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
    # V1.1: Optional judgment gap when user_judgment is provided
    judgment_gap: "JudgmentGap | None" = None


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
    # V1.1
    judgment_gap: "JudgmentGap | None" = None


# ── /iterate ──────────────────────────────────────────────────────────

class IterationDirection(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    expected_impact: str = Field(..., min_length=1)


class IterateResponse(BaseModel):
    directions: list[IterationDirection] = Field(..., min_length=1, max_length=5)
    # V1.1
    judgment_gap: "JudgmentGap | None" = None


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
    user_score: int | None = None
    ai_score: int | None = None
    judgment_gap_summary: str | None = None
    training_focus_tags: str | None = None


class SessionsResponse(BaseModel):
    sessions: list[SessionRecord]
    total: int = Field(..., ge=0)


# ── /upload ───────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    image_id: int = Field(..., description="Database ID of the uploaded image")
    filename: str = Field(..., description="Stored filename (UUID-based)")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    size_bytes: int = Field(..., description="File size in bytes")
    url: str = Field(..., description="URL to view the uploaded image")
    created_at: datetime = Field(..., description="Upload timestamp")


# ── V1.1: Judgment gap ───────────────────────────────────────────────

class JudgmentGap(BaseModel):
    """Comparison result between user self-assessment and AI evaluation."""

    accurate_judgments: list[str] = Field(default_factory=list)
    missed_issues: list[str] = Field(default_factory=list)
    misjudgments: list[str] = Field(default_factory=list)
    commercial_blind_spots: list[str] = Field(default_factory=list)
    aesthetic_blind_spots: list[str] = Field(default_factory=list)
    next_training_focus: list[str] = Field(default_factory=list)
    short_summary: str = Field("", min_length=1)


# ── V1.3: Vision description ─────────────────────────────────────────

class VisionDescription(BaseModel):
    """Structured description of an image produced by a vision adapter."""

    summary: str = Field(..., min_length=1)
    colors: list[str] = Field(default_factory=list)
    composition: str = Field(default="")
    typography: str | None = None
    materials: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    background: str | None = None
    style_keywords: list[str] = Field(default_factory=list)
    potential_issues: list[str] = Field(default_factory=list)
    suggested_prompt_text: str = Field(default="")


class ImageDescribeResponse(BaseModel):
    """Response for POST /images/{image_id}/describe."""
    image_id: int
    description: VisionDescription


# Resolve forward references (JudgmentGap is referenced as a string
# in AnalyzeResponse, CritiqueResponse, and IterateResponse above).
AnalyzeResponse.model_rebuild()
CritiqueResponse.model_rebuild()
IterateResponse.model_rebuild()
