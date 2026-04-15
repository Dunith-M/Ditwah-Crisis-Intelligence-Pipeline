from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from crisis_pipeline.infrastructure.io.file_manager import FileManager


# =========================================================
# 🔹 LEGACY FUNCTION (KEPT)
# =========================================================

def generate_token_report(results: list) -> list:
    """
    Simple transformation of token results.
    (Used in earlier pipeline steps)
    """
    report = []

    for r in results:
        report.append({
            "tokens": r["tokens"],
            "action": r["action"]
        })

    return report


# =========================================================
# 🔹 INDUSTRIAL REPORTING SERVICE (NEW)
# =========================================================

class ReportingService:
    """
    Responsible for:
    - creating structured markdown reports
    - tracking execution metadata
    - summarizing pipeline quality
    """

    def __init__(self):
        self.file_manager = FileManager()

    # -----------------------------------------------------

    def _duration_seconds(self, started_at: str, finished_at: str) -> float:
        start = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(finished_at, "%Y-%m-%d %H:%M:%S")
        return round((end - start).total_seconds(), 2)

    # -----------------------------------------------------

    def create_module_report(
        self,
        report_file: str,
        module_title: str,
        started_at: str,
        finished_at: str,
        model_used: str,
        temperature_used: float,
        input_file_name: str,
        output_file_name: str,
        total_records: int,
        success_count: int,
        failed_count: int,
        warning_count: int,
        summary_lines: List[str],
        raw_response_files: Optional[List[str]] = None,
    ) -> Path:
        """
        Creates a full markdown report for any module.
        """

        duration = self._duration_seconds(started_at, finished_at)

        # 🔹 Raw LLM outputs section
        raw_section = ""
        if raw_response_files:
            raw_lines = "\n".join([f"- `{file}`" for file in raw_response_files])
            raw_section = f"\n## Raw LLM Response Files\n{raw_lines}\n"

        # 🔹 Summary section
        summary_text = "\n".join([f"- {line}" for line in summary_lines])

        report = f"""# {module_title}

## Execution Metadata
- Started at: {started_at}
- Finished at: {finished_at}
- Duration (seconds): {duration}
- Model used: {model_used}
- Temperature used: {temperature_used}
- Input file name: {input_file_name}
- Output file name: {output_file_name}

## Quality Summary
- Total records: {total_records}
- Success count: {success_count}
- Failed count: {failed_count}
- Warning count: {warning_count}

## Summary
{summary_text}
{raw_section}
"""

        return self.file_manager.write_text(report_file, report)

    # -----------------------------------------------------

    def create_token_report(
        self,
        results: List[dict],
        input_file: str,
        output_file: str,
        report_file: str,
    ) -> Path:
        """
        Industrial version of token report with metadata.
        """

        total = len(results)
        summarized = sum(1 for r in results if r["action"] == "summarized")
        allowed = sum(1 for r in results if r["action"] == "allowed")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return self.create_module_report(
            report_file=report_file,
            module_title="Token Guard Report",
            started_at=now,
            finished_at=now,
            model_used="N/A",
            temperature_used=0.0,
            input_file_name=input_file,
            output_file_name=output_file,
            total_records=total,
            success_count=allowed + summarized,
            failed_count=0,
            warning_count=0,
            summary_lines=[
                "Token budget enforcement executed.",
                f"{summarized} records were summarized due to overflow.",
                "No LLM involved unless summarization is upgraded.",
            ],
            raw_response_files=None,
        )
