from crisis_pipeline.infrastructure.llm.model_gateway import LLMGateway
from crisis_pipeline.infrastructure.llm.prompt_loader import PromptLoader
from crisis_pipeline.application.use_cases.run_stability_experiment import (
    generate_drift_commentary,
)


class ReasoningService:
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.llm = LLMGateway()

    def score_incident(self, incident: str) -> str:
        prompt = self.prompt_loader.load("reasoning/cot_incident_scoring.txt")
        final_prompt = (
            prompt
            .replace("{incident}", incident)
            .replace("{incident_input}", incident)
        )
        return self.llm.generate(final_prompt)

    def run_stability_prompt(self, scenario: str, temperature: float = 0.0) -> str:
        prompt = self.prompt_loader.load("reasoning/cot_incident_scoring.txt")
        final_prompt = (
            prompt
            .replace("{incident}", scenario)
            .replace("{incident_input}", scenario)
        )
        llm = LLMGateway({"temperature": temperature})
        return llm.generate(final_prompt)


def generate_stability_report(results, output_path):
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
