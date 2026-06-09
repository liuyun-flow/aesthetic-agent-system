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
    id: str = Field(default="", min_length=1, description="Unique direction id, e.g. dir-1")
    title: str = Field(..., min_length=1, description="Short, punchy name for this direction")
    description: str = Field(default="", description="2-3 sentences describing the visual approach")
    expected_impact: str = Field(default="", description="What this direction would likely improve or change")
    goal: str = Field(default="", description="Core design goal of this iteration")
    visual_changes: str = Field(default="", description="Visual/风格层面的具体变化")
    color_changes: str = Field(default="", description="色彩层面的具体变化")
    typography_changes: str = Field(default="", description="字体排版层面的具体变化")
    layout_changes: str = Field(default="", description="布局构图层面的具体变化")
    commercial_rationale: str = Field(default="", description="商业层面的理由/目标用户考量")
    risk: str = Field(default="", description="Potential risk or downside of this direction")


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


class SessionDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    record_type: RecordType
    work_description: str
    created_at: datetime | None = None
    # User judgment
    user_score: int | None = None
    user_strengths: str | None = None
    user_weaknesses: str | None = None
    user_priority_fixes: str | None = None
    user_target_audience: str | None = None
    user_price_band: str | None = None
    # AI result
    result_json: dict | None = None
    ai_score: int | None = None
    ai_main_problems: str | None = None
    ai_priority_fixes: str | None = None
    # Judgment gap
    judgment_gap_summary: str | None = None
    training_focus_tags: str | None = None
    # V1.7.2: Iteration direction selection + generated prompt
    selected_direction: str | None = None
    prompt_result: dict | None = None


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
    vision_provider: str = "placeholder"
    is_placeholder: bool = True
    warning: str | None = None


# ── V1.4.3: Vision status ────────────────────────────────────────────

# ── V1.5: Training workbench ───────────────────────────────────────

TRAINING_THEMES = [
    "字体与排版",
    "色彩与高级感",
    "构图与留白",
    "材质与质感",
    "价格带判断",
    "商业适配与目标用户",
]


class TodayTrainingResponse(BaseModel):
    theme: str
    tasks: list[str] = Field(default_factory=list)


class CompleteTrainingRequest(BaseModel):
    training_theme: str | None = None
    user_lesson: str | None = None
    next_focus: str | None = None
    after_score: int | None = Field(default=None, ge=0, le=100)


class TrainingStatsResponse(BaseModel):
    total_sessions: int = 0
    completed_sessions: int = 0
    sessions_this_week: int = 0
    current_streak_days: int = 0
    average_user_score: float | None = None
    average_ai_score: float | None = None
    average_score_gap: float | None = None
    common_training_focus_tags: list[str] = Field(default_factory=list)


class WeeklyReviewResponse(BaseModel):
    summary: str = ""
    common_misjudgments: str = ""
    progress_points: str = ""
    recurring_issues: str = ""
    next_week_theme: str = ""
    next_week_tasks: list[str] = Field(default_factory=list)


class VisionStatusResponse(BaseModel):
    vision_provider: str
    is_placeholder: bool
    is_configured: bool
    missing_keys: list[str] = Field(default_factory=list)
    message: str


# ── V1.4: Reference cases ────────────────────────────────────────────

class ReferenceCaseResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    category: str | None = None
    aesthetic_level: str | None = None
    style_tags: str | None = None
    target_audience: str | None = None
    price_band: str | None = None
    image_id: int | None = None
    image_url: str | None = None
    image_description: str | None = None
    ai_description: str | None = None
    notes: str | None = None
    score: int | None = None
    premium_sources: str | None = None
    cheapness_sources: str | None = None
    learn_from_this: str | None = None
    avoid_copying: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # V1.9: Quality fields (computed, not persisted)
    completeness_score: int = 0
    is_training_ready: bool = False
    missing_fields: list[str] = Field(default_factory=list)


class ReferenceCaseListResponse(BaseModel):
    cases: list[ReferenceCaseResponse]
    total: int


# ── V1.9: Case quality audit ─────────────────────────────────────────

class AuditIssue(BaseModel):
    """A single issue found during case quality audit."""
    id: int
    title: str
    aesthetic_level: str | None = None
    completeness_score: int = 0
    is_training_ready: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    reason: str = ""


class DuplicateGroup(BaseModel):
    """A group of possibly duplicate cases."""
    method: str = "title_similarity"
    cases: list[AuditIssue] = Field(default_factory=list)


class CaseAuditResponse(BaseModel):
    """Full case library quality audit report."""
    total_cases: int = 0
    training_ready_count: int = 0
    incomplete_count: int = 0
    average_completeness: float = 0.0
    missing_image: list[AuditIssue] = Field(default_factory=list)
    missing_description: list[AuditIssue] = Field(default_factory=list)
    missing_aesthetic_level: list[AuditIssue] = Field(default_factory=list)
    missing_price_band: list[AuditIssue] = Field(default_factory=list)
    missing_premium_sources: list[AuditIssue] = Field(default_factory=list)
    missing_cheapness_sources: list[AuditIssue] = Field(default_factory=list)
    missing_learning_notes: list[AuditIssue] = Field(default_factory=list)
    possible_duplicates: list[DuplicateGroup] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ── V1.4.1: Generated prompt ─────────────────────────────────────────

class GeneratedPrompt(BaseModel):
    chinese_prompt: str = ""
    english_prompt: str = ""
    negative_prompt: str = ""
    design_notes: list[str] = Field(default_factory=list)
    copywriting_prompt: str = ""
    usage_tips: list[str] = Field(default_factory=list)


class CompareWithReferencesResponse(BaseModel):
    overall_level_estimate: str = ""
    closest_reference_level: str = ""
    stronger_than_low_cases: list[str] = Field(default_factory=list)
    weaker_than_high_cases: list[str] = Field(default_factory=list)
    key_gaps: list[str] = Field(default_factory=list)
    priority_fixes: list[str] = Field(default_factory=list)
    reference_cases_used: list[int] = Field(default_factory=list)
    training_takeaway: str = ""
    next_practice: list[str] = Field(default_factory=list)


# Resolve forward references (JudgmentGap is referenced as a string
# in AnalyzeResponse, CritiqueResponse, and IterateResponse above).
AnalyzeResponse.model_rebuild()
CritiqueResponse.model_rebuild()
IterateResponse.model_rebuild()
