import json
import re
from typing import Any


class JsonCleaner:
    """Extract and parse a JSON object from raw LLM output."""

    def clean(self, raw_text: str) -> dict[str, Any]:
        if not isinstance(raw_text, str):
            raise TypeError("Expected raw_text to be a string.")

        text = raw_text.strip()

        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            text = fenced_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                text = json_match.group(0)

        return json.loads(text)
