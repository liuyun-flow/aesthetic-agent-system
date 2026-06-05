"""Analyzer agent — decomposes a work into aesthetic dimensions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import AnalyzeResponse


ANALYZER_SYSTEM_PROMPT = (
    "You are a professional aesthetic analyst with expertise in visual design, "
    "branding, and art direction. Your role is to decompose a described work into "
    "its aesthetic dimensions and provide constructive, specific analysis.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

ANALYZER_USER_PROMPT_TEMPLATE = """Analyze the following visual work description in detail.
Cover every dimension listed below. Be specific, concrete, and actionable.

Work description:
{work_description}
{image_block}
Return a JSON object with exactly these keys:
- color: Color scheme analysis (palette, harmony, contrast, saturation)
- composition: Composition analysis (balance, hierarchy, white space, focal points)
- typography: Typography / font analysis (readability, pairing, sizing, personality)
- material: Material / texture feel (simulated surfaces, depth, tactility)
- emotion: Emotional impact (mood, atmosphere, psychological response)
- brand_sense: Brand perception (personality, trustworthiness, distinctiveness)
- premium_sources: Sources of premium feel (what elevates the work)
- cheapness_sources: Sources of cheapness (what drags the work down)
- improvement_suggestions: Actionable improvement ideas (prioritized, concrete)

Each value must be a non-empty string with substantive analysis."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    # Try to match a ```json ... ``` block first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    # Try to find the first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class AnalyzerAgent:
    """Produces a structured multi-dimensional aesthetic analysis."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> AnalyzeResponse:
        """Analyze a work description, optionally enriched with an image description."""
        image_block = ""
        if image_description:
            image_block = (
                f"\nAttached image description:\n{image_description}\n"
            )

        messages = [
            {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": ANALYZER_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description,
                    image_block=image_block,
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)

        return AnalyzeResponse.model_validate(data)
