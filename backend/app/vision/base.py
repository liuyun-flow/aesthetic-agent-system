"""Vision adapter protocol — pluggable image-to-text backends.

To add a new vision backend, subclass VisionAdapter and implement
``describe_image`` (plain text) and ``describe_image_structured``
(structured output).  Then register it in ``app.main`` via the
``get_vision_adapter`` dependency.

Current adapters:
- PlaceholderAdapter – returns mock structured descriptions (V1.3 default)
- ManualAdapter – user supplies the description directly (V1.2 compat)
- (future) OpenAIVisionAdapter
- (future) ClaudeVisionAdapter
"""

from abc import ABC, abstractmethod

from app.schemas.responses import VisionDescription


class VisionAdapter(ABC):
    """Protocol for image-to-text vision adapters.

    Each implementation is responsible for turning an image file into a
    natural-language description that the analyzer agent can consume.
    """

    @abstractmethod
    def describe_image(self, image_path: str, hint: str | None = None) -> str:
        """Return a plain-text description of the image at *image_path*.

        Used by the V1.2 manual-description flow.  The *hint* parameter
        carries any user-supplied description text.

        Returns:
            A human-readable description string.
        """
        ...

    def describe_image_structured(self, image_path: str) -> VisionDescription:
        """Return a structured description of the image at *image_path*.

        Used by the V1.3 auto-describe endpoint (``POST /images/{id}/describe``).
        Default implementation wraps ``describe_image`` into a simple
        VisionDescription; subclasses should override for richer output.

        Returns:
            A VisionDescription with detailed aesthetic analysis.
        """
        text = self.describe_image(image_path)
        return VisionDescription(
            summary=text,
            colors=[],
            composition="",
            typography=None,
            materials=[],
            subjects=[],
            background=None,
            style_keywords=[],
            potential_issues=[],
            suggested_prompt_text=text,
        )
