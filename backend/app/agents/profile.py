"""Profile agent — summarizes training history into a user profile."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import ProfileResponse


PROFILE_SYSTEM_PROMPT = (
    "You are a design coach who reviews a student's training history and "
    "produces insightful, personalized feedback. You identify patterns, "
    "preferences, blind spots, and growth areas.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

PROFILE_USER_PROMPT_TEMPLATE = """Review the following training history from a user of
an aesthetic training system. Based on the patterns you observe, produce a profile summary.

Training history (JSON array of records):
{history_json}

Return a JSON object with exactly these keys:
- preferences: string (summarize the user's apparent design preferences — styles, colors, moods they gravitate toward)
- common_mistakes: string (patterns of weaknesses or recurring issues across their work)
- next_week_focus: string (specific, actionable focus areas for the coming week's training)

Be constructive and encouraging. Ground every observation in the provided history."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class ProfileAgent:
    """Summarizes training history into a user aesthetic profile."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, history: list[dict[str, Any]], total_sessions: int) -> ProfileResponse:
        if not history:
            return ProfileResponse(
                preferences="Not enough data yet. Complete a few analyses to build your profile.",
                common_mistakes="Not enough data yet.",
                next_week_focus="Start by submitting works for analysis and critique.",
                total_sessions=0,
            )

        history_json = json.dumps(history, ensure_ascii=False, indent=2, default=str)

        messages = [
            {"role": "system", "content": PROFILE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": PROFILE_USER_PROMPT_TEMPLATE.format(
                    history_json=history_json
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

        return ProfileResponse.model_validate({**data, "total_sessions": total_sessions})
