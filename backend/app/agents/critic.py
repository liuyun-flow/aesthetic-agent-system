"""Critic agent — scores a work across aesthetic dimensions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import CritiqueResponse


CRITIC_SYSTEM_PROMPT = (
    "You are a professional design critic. You evaluate visual work with "
    "objective rigor, assigning numerical scores (1-10) across aesthetic dimensions "
    "and identifying specific, actionable issues.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

CRITIC_USER_PROMPT_TEMPLATE = """Critique the following visual work description.
Score each dimension on a 1-10 scale (1 = poor, 10 = outstanding).
Be honest and precise — inflated scores help no one.

Work description:
{work_description}

Return a JSON object with exactly these keys:
- total_score: number (weighted average of all dimension scores, 1-10)
- dimensions: object with number scores for each key: color, composition, typography, material, emotion, brand_sense
- main_issues: array of strings (top 3-5 problems, each a concrete sentence)
- cheapness_sources: array of strings (elements that make the work feel cheap / low-budget)
- priority_fixes: array of strings (ordered list of the most impactful fixes to apply first)

Each score must be between 1 and 10."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class CriticAgent:
    """Produces a scored critique with identified issues and priority fixes."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, work_description: str) -> CritiqueResponse:
        messages = [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": CRITIC_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)

        return CritiqueResponse.model_validate(data)
