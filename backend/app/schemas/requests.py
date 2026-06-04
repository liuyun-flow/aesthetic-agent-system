"""Pydantic request schemas."""

from pydantic import BaseModel, ConfigDict, Field


class WorkDescriptionRequest(BaseModel):
    """Request body for /analyze, /critique, /iterate."""

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
