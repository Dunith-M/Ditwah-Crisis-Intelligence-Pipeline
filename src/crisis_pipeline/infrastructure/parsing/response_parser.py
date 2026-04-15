from __future__ import annotations

import ast
import json
import re
from typing import Dict, Optional
import yaml

from crisis_pipeline.infrastructure.logging.logger import LoggerFactory


class ResponseParser:

    def __init__(self):
        logger_factory = LoggerFactory()
        self.warning_logger = logger_factory.get_warning_logger()

    # =========================================================
    # 🔹 CLASSIFICATION PARSER
    # =========================================================

    def parse_classification(
        self,
        text: str,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        raw_response_file: Optional[str] = None,
    ) -> Dict:
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
            self.warning_logger.warning(
                f"Invalid classification parse | input={input_file} | output={output_file} | raw_file={raw_response_file}"
            )
            raise ValueError("Invalid classification output")

        return result

    # =========================================================
    # 🔹 MESSAGE CLASSIFICATION (CUSTOM FORMAT)
    # =========================================================

    def parse_message_classification(
        self,
        text: str,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        raw_response_file: Optional[str] = None,
    ) -> Dict:
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

        except Exception as e:
            self.warning_logger.warning(
                f"Message classification parse error | input={input_file} | raw_file={raw_response_file} | error={str(e)}"
            )

        return result

    # =========================================================
    # 🔹 JSON PARSER (ADVANCED FALLBACK SYSTEM)
    # =========================================================

    def parse_json(
        self,
        text: str,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        raw_response_file: Optional[str] = None,
    ) -> Dict:
        try:
            return json.loads(text)

        except json.JSONDecodeError as e:

            # 🔹 Try Python dict
            python_dict_result = self._parse_python_dict(text)
            if python_dict_result:
                return python_dict_result

            # 🔹 Try YAML
            yaml_result = self._parse_yaml_object(text)
            if yaml_result:
                return yaml_result

            # 🔹 Try fenced JSON
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

            # 🔹 Try inline JSON
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

            # 🔹 Try scorecard parser
            parsed_scorecard = self._parse_incident_scorecard(text)
            if parsed_scorecard:
                return parsed_scorecard

            # 🔴 FINAL FAILURE → LOG IT
            self.warning_logger.warning(
                f"Invalid JSON parse | input={input_file} | output={output_file} | raw_file={raw_response_file} | error={str(e)}"
            )

            raise ValueError("Invalid JSON output from LLM")

    # =========================================================
    # 🔹 FALLBACK PARSERS
    # =========================================================

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

    # =========================================================
    # 🔹 INCIDENT SCORECARD PARSER
    # =========================================================

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


# =========================================================
# 🔹 FUNCTIONAL SHORTCUT
# =========================================================

def parse_classification(text: str) -> Dict:
    return ResponseParser().parse_message_classification(text)
