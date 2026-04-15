from __future__ import annotations

from typing import List, Dict

from crisis_pipeline.infrastructure.llm.model_gateway import ModelGateway
from crisis_pipeline.infrastructure.llm.prompt_loader import load_prompt
from crisis_pipeline.infrastructure.parsing.response_parser import ResponseParser
from crisis_pipeline.application.services.reporting_service import ReportingService


class ClassificationService:
    """
    Industrial Classification Service:
    - Supports single + batch classification
    - Stores raw LLM outputs
    - Logs parsing failures
    - Generates reports
    """

    def __init__(self):
        self.model_gateway = ModelGateway()
        self.prompt_loader = load_prompt  # keeping your function style
        self.parser = ResponseParser()
        self.reporting_service = ReportingService()

    # =========================================================
    # 🔹 LEGACY METHOD (KEPT)
    # =========================================================

    def classify(self, message: str) -> dict:
        """
        Single message classification (backward compatible)
        """

        prompt_template = self.prompt_loader(
            "prompts/classification/few_shot_classifier.txt"
        )

        prompt = prompt_template.replace("{{message}}", message)

        audit = self.model_gateway.generate(
            prompt=prompt,
            module_name="classification",
            input_file="single_input",
            output_file="single_output",
        )

        parsed = self.parser.parse_classification(
            text=audit["raw_response"],
            input_file="single_input",
            output_file="single_output",
            raw_response_file=audit["raw_response_file"],
        )

        return parsed

    # =========================================================
    # 🔹 INDUSTRIAL METHOD (NEW)
    # =========================================================

    def classify_messages(
        self,
        messages: List[str],
        input_file: str,
        output_file: str,
        report_file: str = "outputs/reports/classification_report.md",
        prompt_path: str = "prompts/classification/few_shot_classifier.txt",
    ) -> List[Dict]:

        prompt_template = self.prompt_loader(prompt_path)

        results = []
        raw_files = []
        success_count = 0
        failed_count = 0
        warning_count = 0

        first_started_at = None
        last_finished_at = None

        for message in messages:
            prompt = f"{prompt_template}\n\nMessage:\n{message}"

            audit = self.model_gateway.generate(
                prompt=prompt,
                module_name="classification",
                input_file=input_file,
                output_file=output_file,
            )

            if first_started_at is None:
                first_started_at = audit["started_at"]

            last_finished_at = audit["finished_at"]
            raw_files.append(audit["raw_response_file"])

            try:
                parsed = self.parser.parse_classification(
                    text=audit["raw_response"],
                    input_file=input_file,
                    output_file=output_file,
                    raw_response_file=audit["raw_response_file"],
                )

                parsed["message"] = message
                results.append(parsed)
                success_count += 1

            except Exception:
                failed_count += 1
                warning_count += 1

                results.append(
                    {
                        "message": message,
                        "label": "PARSE_ERROR",
                        "confidence": None,
                    }
                )

        # 🔹 REPORT GENERATION
        self.reporting_service.create_module_report(
            report_file=report_file,
            module_title="Classification Report",
            started_at=first_started_at or "N/A",
            finished_at=last_finished_at or "N/A",
            model_used=self.model_gateway.model_name,
            temperature_used=self.model_gateway.temperature,
            input_file_name=input_file,
            output_file_name=output_file,
            total_records=len(messages),
            success_count=success_count,
            failed_count=failed_count,
            warning_count=warning_count,
            summary_lines=[
                "Few-shot classification executed.",
                "Raw LLM outputs stored for auditability.",
                "Parsing errors converted into warnings (no silent failures).",
            ],
            raw_response_files=raw_files,
        )

        return results