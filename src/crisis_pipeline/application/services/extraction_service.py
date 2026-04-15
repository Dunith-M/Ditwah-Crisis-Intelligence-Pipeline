from __future__ import annotations

from typing import List, Dict

from crisis_pipeline.application.services.reporting_service import ReportingService
from crisis_pipeline.infrastructure.parsing.response_parser import ResponseParser
from crisis_pipeline.infrastructure.logging.logger import LoggerFactory


class ExtractionService:
    """
    Industrial Extraction Service

    Features:
    - LLM-based JSON extraction
    - raw response storage
    - parse validation
    - failure tracking
    - reporting
    - logging (NEW)
    """

    def __init__(self, model_gateway, prompt_loader):
        self.model_gateway = model_gateway
        self.prompt_loader = prompt_loader
        self.parser = ResponseParser()
        self.reporting_service = ReportingService()

        # 🔹 NEW: logging
        logger_factory = LoggerFactory()
        self.app_logger = logger_factory.get_app_logger()
        self.warning_logger = logger_factory.get_warning_logger()

    def extract_news_events(
        self,
        news_items: List[str],
        input_file: str,
        output_file: str,
        report_file: str = "outputs/reports/extraction_validation_report.md",
        prompt_path: str = "prompts/extraction/json_extract.txt",
    ) -> List[Dict]:

        prompt_template = self.prompt_loader.load(prompt_path)

        results = []
        raw_files = []
        success_count = 0
        failed_count = 0
        warning_count = 0

        first_started_at = None
        last_finished_at = None

        for idx, news in enumerate(news_items):
            prompt = f"{prompt_template}\n\nNews:\n{news}"

            audit = self.model_gateway.generate(
                prompt=prompt,
                module_name="extraction",
                input_file=input_file,
                output_file=output_file,
            )

            if first_started_at is None:
                first_started_at = audit["started_at"]

            last_finished_at = audit["finished_at"]
            raw_files.append(audit["raw_response_file"])

            try:
                parsed = self.parser.parse_json(
                    text=audit["raw_response"],
                    input_file=input_file,
                    output_file=output_file,
                    raw_response_file=audit["raw_response_file"],
                )

                results.append(parsed)
                success_count += 1

                self.app_logger.info(
                    f"Extraction success | index={idx} | input={input_file}"
                )

            except Exception as e:
                failed_count += 1
                warning_count += 1

                self.warning_logger.warning(
                    f"Extraction failed | index={idx} | input={input_file} | raw_file={audit['raw_response_file']} | error={str(e)}"
                )

                results.append(
                    {
                        "event": None,
                        "status": "INVALID_JSON",
                        "raw_response_file": audit["raw_response_file"],
                    }
                )

        # 🔹 REPORT
        self.reporting_service.create_module_report(
            report_file=report_file,
            module_title="Extraction Validation Report",
            started_at=first_started_at or "N/A",
            finished_at=last_finished_at or "N/A",
            model_used=self.model_gateway.model_name,
            temperature_used=self.model_gateway.temperature,
            input_file_name=input_file,
            output_file_name=output_file,
            total_records=len(news_items),
            success_count=success_count,
            failed_count=failed_count,
            warning_count=warning_count,
            summary_lines=[
                "JSON extraction completed.",
                "Invalid JSON outputs were logged to warnings.log.",
                "Raw extraction outputs stored for auditability.",
                "Each failure traceable via raw response file.",
            ],
            raw_response_files=raw_files,
        )

        self.app_logger.info(
            f"Extraction completed | total={len(news_items)} | success={success_count} | failed={failed_count}"
        )

        return results