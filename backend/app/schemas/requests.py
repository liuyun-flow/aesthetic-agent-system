"""Pydantic request schemas."""

from pydantic import BaseModel, ConfigDict, Field


class UserJudgment(BaseModel):
    """Optional user self-assessment submitted alongside a work description.

    All fields are optional — when omitted the backend runs the old
    agent-only flow.  When provided the comparator agent contrasts the
    user's judgment against the AI evaluation.
    """

    score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] | None = Field(default=None, max_length=10)
    weaknesses: list[str] | None = Field(default=None, max_length=10)
    priority_fixes: list[str] | None = Field(default=None, max_length=10)
    target_audience: str | None = Field(default=None, max_length=200)
    price_band: str | None = Field(default=None, max_length=100)


class WorkDescriptionRequest(BaseModel):
    """Request body for /analyze, /critique, /iterate.

    For /analyze, the optional ``image_id`` and ``image_description``
    fields allow attaching a previously uploaded image.  When both are
    set the manual vision adapter passes ``image_description`` through
    to the analyzer agent.

    The optional ``user_judgment`` field (V1.1) enables the training
    loop: the backend compares the user's self-assessment against the
    AI evaluation and returns a judgment gap analysis.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    work_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Description of the visual work to be evaluated",
        examples=[
            "A minimalist landing page with a white background, "
            "sans-serif font, and a single blue CTA button."
        ],
    )

    image_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional ID of a previously uploaded image (see POST /upload).",
    )

    image_description: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description=(
            "Manual image description. Required when image_id is set "
            "and using the ManualAdapter (MVP default)."
        ),
    )

    user_judgment: UserJudgment | None = Field(
        default=None,
        description="Optional user self-assessment for judgment gap analysis.",
    )
