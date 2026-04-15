import ast
import json
import re
from typing import Dict
import yaml


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
            python_dict_result = self._parse_python_dict(text)
            if python_dict_result:
                return python_dict_result

            yaml_result = self._parse_yaml_object(text)
            if yaml_result:
                return yaml_result

            fenced_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if fenced_json:
                fenced_text = fenced_json.group(1)
                try:
                    return json.loads(fenced_text)
                except json.JSONDecodeError:
                    python_dict_result = self._parse_python_dict(fenced_text)
                    if python_dict_result:
                        return python_dict_result
                    yaml_result = self._parse_yaml_object(fenced_text)
                    if yaml_result:
                        return yaml_result

            inline_json = re.search(r"(\{.*\})", text, re.DOTALL)
            if inline_json:
                inline_text = inline_json.group(1)
                try:
                    return json.loads(inline_text)
                except json.JSONDecodeError:
                    python_dict_result = self._parse_python_dict(inline_text)
                    if python_dict_result:
                        return python_dict_result
                    yaml_result = self._parse_yaml_object(inline_text)
                    if yaml_result:
                        return yaml_result

            parsed_scorecard = self._parse_incident_scorecard(text)
            if parsed_scorecard:
                return parsed_scorecard

            raise ValueError("Invalid JSON output from LLM")

    def _parse_python_dict(self, text: str) -> Dict:
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return {}

        return parsed if isinstance(parsed, dict) else {}

    def _parse_yaml_object(self, text: str) -> Dict:
        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError:
            return {}

        return parsed if isinstance(parsed, dict) else {}

    def _parse_incident_scorecard(self, text: str) -> Dict:
        field_map = {
            "people impact": "people_impact",
            "severity": "severity",
            "urgency": "urgency",
            "accessibility": "accessibility",
            "final score": "total_score",
            "reason": "reason",
        }
        result = {}

        for line in text.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            mapped_key = field_map.get(key.strip().lower())
            if not mapped_key:
                continue

            cleaned_value = value.strip()
            if mapped_key == "reason":
                result[mapped_key] = cleaned_value
                continue

            number_match = re.search(r"-?\d+", cleaned_value)
            if number_match:
                result[mapped_key] = int(number_match.group())

        if {"accessibility", "total_score"}.issubset(result):
            return result

        return {}


def parse_classification(text: str) -> Dict:
    return ResponseParser().parse_message_classification(text)
