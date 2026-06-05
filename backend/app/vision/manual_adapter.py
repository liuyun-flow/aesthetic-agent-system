"""Manual vision adapter — the user provides the image description.

This adapter does **not** call any vision model; it simply returns the
user-supplied ``hint`` verbatim.  It also supports structured output
for the V1.3 auto-describe flow (wraps the hint into a minimal
VisionDescription so the new endpoint works).
"""

from app.vision.base import VisionAdapter
from app.schemas.responses import VisionDescription


class ManualAdapter(VisionAdapter):
    """Returns the user-provided hint as the image description.

    When the user calls ``POST /analyze`` with both ``image_id`` and
    ``image_description``, this adapter passes the description through
    so the analyzer agent can incorporate it.
    """

    def describe_image(self, image_path: str, hint: str | None = None) -> str:
        if not hint:
            raise ValueError(
                "ManualAdapter requires an image_description. "
                "Include 'image_description' in the request body, "
                "or switch to a real vision adapter later."
            )
        return hint

    def describe_image_structured(self, image_path: str) -> VisionDescription:
        # Manual adapter can't really analyze an image without a hint.
        # This method exists for interface completeness; the auto-describe
        # endpoint should use PlaceholderAdapter or a real vision adapter.
        return VisionDescription(
            summary="No automatic description available with ManualAdapter.",
            colors=[],
            composition="",
            typography=None,
            materials=[],
            subjects=[],
            background=None,
            style_keywords=[],
            potential_issues=[],
            suggested_prompt_text="",
        )
