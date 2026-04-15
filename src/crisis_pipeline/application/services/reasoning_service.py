from __future__ import annotations

from typing import Any, List, Dict

from crisis_pipeline.infrastructure.llm.model_gateway import LLMGateway
from crisis_pipeline.infrastructure.llm.prompt_loader import PromptLoader
from crisis_pipeline.application.use_cases.run_stability_experiment import (
    generate_drift_commentary,
)

from crisis_pipeline.application.services.reporting_service import ReportingService
from crisis_pipeline.infrastructure.logging.logger import LoggerFactory


class ReasoningService:
    """
    Industrial Reasoning Service

    Supports:
    - incident scoring
    - stability testing
    - logistics reasoning

    Also provides:
    - audit logging
    - raw response storage
    - reporting
    """

    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.model_gateway = LLMGateway()
        self.reporting_service = ReportingService()
        self.app_logger = LoggerFactory().get_app_logger()

    # =========================================================
    # 🔹 LEGACY METHODS (KEPT)
    # =========================================================

    def score_incident(self, incident: str) -> Dict[str, Any]:
        prompt = self.prompt_loader.load("reasoning/cot_incident_scoring.txt")

        final_prompt = (
            prompt
            .replace("{incident}", incident)
            .replace("{incident_input}", incident)
        )

        incident_score_schema = {
            "type": "object",
            "properties": {
                "people_impact": {"type": "integer"},
                "severity": {"type": "integer"},
                "urgency": {"type": "integer"},
                "accessibility": {"type": "integer"},
                "total_score": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": [
                "people_impact",
                "severity",
                "urgency",
                "accessibility",
                "total_score",
                "reason",
            ],
        }

        scoring_gateway = LLMGateway({"temperature": 0.1, "max_tokens": 1024})

        audit = scoring_gateway.generate(
            prompt=final_prompt,
            module_name="incident_scoring",
            input_file="single_input",
            output_file="single_output",
            response_mime_type="application/json",
            response_schema=incident_score_schema,
        )

        return audit

    def run_stability_prompt(self, scenario: str, temperature: float = 0.0) -> str:
        prompt = self.prompt_loader.load("reasoning/cot_incident_scoring.txt")

        final_prompt = (
            prompt
            .replace("{incident}", scenario)
            .replace("{incident_input}", scenario)
        )

        llm = LLMGateway({"temperature": temperature})

        audit = llm.generate(
            prompt=final_prompt,
            module_name="stability",
            input_file="single_input",
            output_file="single_output",
        )

        return audit["raw_response"]

    # =========================================================
    # 🔹 INDUSTRIAL BATCH METHOD (NEW CORE)
    # =========================================================

    def run_reasoning_batch(
        self,
        items: List[str],
        input_file: str,
        output_file: str,
        module_name: str,
        report_file: str,
        prompt_path: str,
    ) -> List[Dict]:

        prompt_template = self.prompt_loader.load(prompt_path)

        results = []
        raw_files = []
        success_count = 0
        failed_count = 0

        first_started_at = None
        last_finished_at = None

        for item in items:
            prompt = f"{prompt_template}\n\nInput:\n{item}"

            audit = self.model_gateway.generate(
                prompt=prompt,
                module_name=module_name,
                input_file=input_file,
                output_file=output_file,
            )

            if first_started_at is None:
                first_started_at = audit["started_at"]

            last_finished_at = audit["finished_at"]
            raw_files.append(audit["raw_response_file"])

            try:
                results.append(
                    {
                        "input": item,
                        "reasoning_output": audit["raw_response"],
                    }
                )
                success_count += 1

            except Exception:
                failed_count += 1

                results.append(
                    {
                        "input": item,
                        "reasoning_output": None,
                    }
                )

        # 🔹 REPORT GENERATION
        self.reporting_service.create_module_report(
            report_file=report_file,
            module_title=f"{module_name.replace('_', ' ').title()} Report",
            started_at=first_started_at or "N/A",
            finished_at=last_finished_at or "N/A",
            model_used=self.model_gateway.model_name,
            temperature_used=self.model_gateway.temperature,
            input_file_name=input_file,
            output_file_name=output_file,
            total_records=len(items),
            success_count=success_count,
            failed_count=failed_count,
            warning_count=failed_count,
            summary_lines=[
                f"{module_name} reasoning completed.",
                "Raw LLM reasoning outputs stored for auditability.",
                "Execution metadata captured for traceability.",
            ],
            raw_response_files=raw_files,
        )

        return results


# =========================================================
# 🔹 LEGACY REPORT (KEPT)
# =========================================================

def generate_stability_report(results, output_path):
    """
    Old-style manual report (still usable)
    """

    lines = ["# Stability Experiment Report\n"]

    for i, res in enumerate(results, start=1):
        lines.append(f"## Scenario {i}")
        lines.append(f"**Input:** {res['scenario']}\n")

        lines.append("### Runs (temperature=1.0):")
        for run in res["runs_temp_1"]:
            lines.append(f"- {run}")

        lines.append("\n### Deterministic Run (temperature=0.0):")
        lines.append(f"- {res['run_temp_0']}\n")

        drift = generate_drift_commentary(res["runs_temp_1"])

        lines.append("### Drift Analysis:")
        if drift:
            for d in drift:
                lines.append(f"- {d}")
        else:
            lines.append("- Stable output")

        lines.append("\n---\n")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
