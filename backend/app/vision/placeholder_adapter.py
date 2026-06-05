"""Placeholder vision adapter — returns mock structured descriptions.

This is the V1.3 default.  It does **not** call any real vision API;
it returns a hard-coded example VisionDescription.  Swap to a real
adapter by setting ``VISION_PROVIDER`` in your ``.env`` file.
"""

from app.vision.base import VisionAdapter
from app.schemas.responses import VisionDescription


_MOCK_DESCRIPTION = VisionDescription(
    summary=(
        "A minimalist product photograph featuring a white frosted glass "
        "candle on a cream-colored surface, with soft natural lighting "
        "and subtle botanical accents in the background."
    ),
    colors=["cream white", "soft beige", "sage green", "pale pink"],
    composition=(
        "Centered subject with strong negative space. The candle sits "
        "slightly off-center using the rule of thirds, with a shallow "
        "depth of field that blurs the background botanicals."
    ),
    typography=None,
    materials=["frosted glass", "natural wax", "ceramic", "linen"],
    subjects=["scented candle", "botanical sprig"],
    background="Cream-colored surface with out-of-focus eucalyptus and dried flowers.",
    style_keywords=["minimalist", "premium", "lifestyle", "Scandinavian", "clean"],
    potential_issues=[
        "Lack of human element may reduce emotional connection.",
        "Very low contrast between candle and background could make the product hard to distinguish in thumbnail view.",
        "No visible brand logo or label — brand recall may suffer.",
    ],
    suggested_prompt_text=(
        "A minimalist product shot of a white frosted glass candle on a "
        "cream background. Soft natural light. Eucalyptus and dried "
        "flowers blurred in the background. Clean, premium, Scandinavian "
        "aesthetic. Shallow depth of field. Centered composition with "
        "strong negative space."
    ),
)


class PlaceholderAdapter(VisionAdapter):
    """Returns a fixed mock structured description.

    Does not read the actual image file — always returns the same
    example description.  Useful for testing and development when no
    real vision API key is available.
    """

    def describe_image(self, image_path: str, hint: str | None = None) -> str:
        return _MOCK_DESCRIPTION.suggested_prompt_text

    def describe_image_structured(self, image_path: str) -> VisionDescription:
        return _MOCK_DESCRIPTION
