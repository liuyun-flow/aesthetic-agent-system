"""Iterator agent — proposes 3-5 alternative design directions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import IterateResponse


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
{image_block}
Return a JSON object with exactly this key:
- directions: array of objects, each with:
    - id: string (e.g. "dir-1", "dir-2", "dir-3", "dir-4")
    - title: string (a short, punchy name for this direction)
    - description: string (2-3 sentences describing the overall visual approach)
    - expected_impact: string (what this direction would likely improve or change)
    - goal: string (core design goal — one sentence on what this direction aims to achieve)
    - visual_changes: string (specific visual/style changes: illustration→photography, flat→skeuomorphic, etc.)
    - color_changes: string (specific color palette changes: which colors to adopt, which to drop, saturation/contrast shifts)
    - typography_changes: string (font changes: serif→sans, weight adjustments, hierarchy shifts, font pairing)
    - layout_changes: string (layout/composition changes: grid structure, white space, focal points, information density)
    - commercial_rationale: string (business reasoning: target audience fit, price band alignment, brand positioning)
    - risk: string (potential downside or risk: might alienate existing users, might feel too trendy, might reduce readability, etc.)

Aim for 4 directions. Make them diverse in style, mood, and strategy.
Write all field values IN CHINESE (中文)."""


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

    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> IterateResponse:
        image_block = ""
        if image_description:
            image_block = f"\nAttached image description:\n{image_description}\n"

        messages = [
            {"role": "system", "content": ITERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": ITERATOR_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description,
                    image_block=image_block,
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

        if isinstance(data.get("directions"), list):
            data = {**data, "directions": data["directions"][:5]}
            # Ensure each direction has an id (auto-assign if missing)
            for i, d in enumerate(data["directions"]):
                if isinstance(d, dict) and not d.get("id"):
                    d["id"] = f"dir-{i + 1}"

        return IterateResponse.model_validate(data)
