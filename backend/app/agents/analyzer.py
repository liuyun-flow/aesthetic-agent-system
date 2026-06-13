"""Analyzer agent — decomposes a work into aesthetic dimensions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.agents.design_knowledge import DESIGN_KNOWLEDGE, EVIDENCE_RULES
from app.schemas.responses import AnalyzeResponse


ANALYZER_SYSTEM_PROMPT = (
    "You are a senior art director doing aesthetic training analysis. "
    "You judge work strictly against the design-knowledge base below, citing "
    "principles by name so the trainee learns transferable rules.\n\n"
    f"{DESIGN_KNOWLEDGE}\n"
    f"{EVIDENCE_RULES}\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

ANALYZER_USER_PROMPT_TEMPLATE = """Analyze the following visual work description in detail.
First infer the work's commercial intent (audience, price band, scenario), then judge
every dimension against the knowledge base for THAT intent. Be specific and concrete.

Work description:
{work_description}
{image_block}
Return a JSON object with exactly these keys:
- color: Color scheme analysis (palette, harmony, contrast, saturation)
- composition: Composition analysis (balance, hierarchy, white space, focal points)
- typography: Typography / font analysis (readability, pairing, sizing, personality)
- material: Material / texture feel (simulated surfaces, depth, tactility)
- emotion: Emotional impact (mood, atmosphere, psychological response)
- brand_sense: Brand perception (personality, trustworthiness, distinctiveness, intent fit)
- premium_sources: Sources of premium feel (name the specific signifiers present)
- cheapness_sources: Sources of cheapness (name the specific signifiers present)
- improvement_suggestions: Actionable improvement ideas (prioritized, concrete, principle-based)

Requirements:
- Each value must be a non-empty string with substantive analysis.
- Every claim must point to a concrete element from the description and name the
  design principle it honors or violates. If the description lacks information for
  a dimension, say so explicitly instead of inventing details.
- Write all field values IN CHINESE (中文)."""


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
