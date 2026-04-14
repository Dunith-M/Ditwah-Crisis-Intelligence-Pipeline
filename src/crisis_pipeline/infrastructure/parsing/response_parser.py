import json
import re
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

    def parse_message_classification(self, text: str) -> Dict:
        """
        Expected format:
        district: X
        intent: Y
        priority: Z
        """

        result = {
            "district": None,
            "intent": None,
            "priority": None
        }

        try:
            district_match = re.search(r"district:\s*(.*)", text, re.IGNORECASE)
            intent_match = re.search(r"intent:\s*(.*)", text, re.IGNORECASE)
            priority_match = re.search(r"priority:\s*(.*)", text, re.IGNORECASE)

            if district_match:
                result["district"] = district_match.group(1).strip()

            if intent_match:
                result["intent"] = intent_match.group(1).strip()

            if priority_match:
                result["priority"] = priority_match.group(1).strip()

        except Exception:
            pass

        return result

    def parse_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON output from LLM")