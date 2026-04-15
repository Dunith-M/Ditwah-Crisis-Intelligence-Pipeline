from __future__ import annotations

from typing import Dict, List
from datetime import datetime

from crisis_pipeline.infrastructure.token.counter import TokenCounter
from crisis_pipeline.application.services.reporting_service import ReportingService


class TokenService:
    """
    Industrial Token Control Service

    Features:
    - token counting
    - 3-level decision (allow / summarize / block)
    - batch processing
    - reporting + metadata
    """

    def __init__(self, max_tokens: int = 150):
        self.counter = TokenCounter()
        self.max_tokens = max_tokens
        self.reporting_service = ReportingService()

    # =========================================================
    # 🔹 SUMMARIZATION (PLACEHOLDER)
    # =========================================================

    def summarize(self, text: str) -> str:
        """
        Simple fallback summarization.
        In real system → replace with LLM call.
        """
        return text[:100] + "..." if len(text) > 100 else text

    # =========================================================
    # 🔹 SINGLE PROCESS
    # =========================================================

    def process(self, text: str) -> Dict:
        token_count = self.counter.count(text)

        result = {
            "original_text": text,
            "processed_text": text,
            "tokens": token_count,
            "action": "allowed",
        }

        # ✅ within limit → allow
        if token_count <= self.max_tokens:
            return result

        # 🔴 very large → block
        if token_count > self.max_tokens * 2:
            result["processed_text"] = ""
            result["action"] = "blocked"
            return result

        # 🟡 moderate → summarize
        summarized = self.summarize(text)
        result["processed_text"] = summarized
        result["action"] = "summarized"

        return result

    # =========================================================
    # 🔹 BATCH PROCESS (INDUSTRIAL)
    # =========================================================

    def process_batch(
        self,
        texts: List[str],
        input_file: str,
        output_file: str,
        report_file: str = "outputs/reports/token_guard_report.md",
    ) -> List[Dict]:

        results = [self.process(text) for text in texts]

        # 🔹 Metrics
        allowed_count = sum(1 for r in results if r["action"] == "allowed")
        summarized_count = sum(1 for r in results if r["action"] == "summarized")
        blocked_count = sum(1 for r in results if r["action"] == "blocked")

        # 🔹 Metadata
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        finished_at = started_at

        # 🔹 REPORT
        self.reporting_service.create_module_report(
            report_file=report_file,
            module_title="Token Guard Report",
            started_at=started_at,
            finished_at=finished_at,
            model_used="N/A",
            temperature_used=0.0,
            input_file_name=input_file,
            output_file_name=output_file,
            total_records=len(texts),
            success_count=allowed_count + summarized_count,
            failed_count=blocked_count,
            warning_count=0,
            summary_lines=[
                "Token budget enforcement completed.",
                f"{allowed_count} records allowed.",
                f"{summarized_count} records summarized.",
                f"{blocked_count} records blocked due to excessive length.",
                "System prevents extreme token overflow before LLM call.",
            ],
            raw_response_files=None,
        )

        return results
