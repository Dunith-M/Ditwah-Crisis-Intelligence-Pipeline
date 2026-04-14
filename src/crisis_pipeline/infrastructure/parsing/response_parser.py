import json
from typing import Dict


class ResponseParser:

    def parse_classification(self, text: str) -> Dict:
        """
        Expected format:
        Label: X
        Confidence: Y
        """

        result = {}

        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip().lower()] = value.strip()

        if "label" not in result:
            raise ValueError("Invalid classification output")

        return result

    def parse_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON output from LLM")