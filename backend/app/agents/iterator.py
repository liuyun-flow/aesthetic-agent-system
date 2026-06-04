"""Iterator agent — proposes 3-5 alternative design directions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import IterateResponse, IterationDirection


ITERATOR_SYSTEM_PROMPT = (
    "You are a creative design director who excels at generating divergent "
    "design directions. For any given work, you can envision multiple compelling "
    "alternatives across different styles, moods, and strategies.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

ITERATOR_USER_PROMPT_TEMPLATE = """You are given a visual work description.
Propose 3-5 distinct iteration directions. Each direction should represent a
meaningfully different creative strategy — not minor tweaks of the same idea.

Work description:
{work_description}

Return a JSON object with exactly this key:
- directions: array of objects, each with:
    - title: string (a short, punchy name for this direction)
    - description: string (2-3 sentences describing the visual approach)
    - expected_impact: string (what this direction would likely improve or change)

Aim for 4 directions. Make them diverse in style, mood, and strategy."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class IteratorAgent:
    """Generates 3-5 distinct iteration directions for a work."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, work_description: str) -> IterateResponse:
        messages = [
            {"role": "system", "content": ITERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": ITERATOR_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)

        raw_directions = data.get("directions", [])
        directions = [
            IterationDirection(
                title=d.get("title", ""),
                description=d.get("description", ""),
                expected_impact=d.get("expected_impact", ""),
            )
            for d in raw_directions
        ]

        return IterateResponse(directions=directions[:5])
