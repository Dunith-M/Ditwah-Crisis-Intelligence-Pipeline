from crisis_pipeline.infrastructure.io.text_loader import TextLoader

def load_scenarios(path: str):
    loader = TextLoader()
    return loader.load_lines(path)


def run_experiment(scenarios, reasoning_service):
    results = []

    for scenario in scenarios:
        scenario_result = {
            "scenario": scenario,
            "runs_temp_1": [],
            "run_temp_0": None
        }

        #  High randomness (3 runs)
        for _ in range(3):
            output = reasoning_service.run_stability_prompt(
                scenario,
                temperature=1.0
            )
            scenario_result["runs_temp_1"].append(output)

        #  Deterministic (1 run)
        scenario_result["run_temp_0"] = reasoning_service.run_stability_prompt(
            scenario,
            temperature=0.0
        )

        results.append(scenario_result)

    return results


def analyze_differences(runs):
    base = runs[0]
    differences = []

    for i, run in enumerate(runs[1:], start=1):
        if run != base:
            differences.append({
                "run_index": i,
                "difference": True
            })

    return differences



def generate_drift_commentary(runs):
    commentary = []

    unique_outputs = list(set(runs))

    if len(unique_outputs) > 1:
        commentary.append("Inconsistent outputs across runs")

    # Simple heuristics
    for run in runs:
        if "evacuate" in run.lower() and "stay" in run.lower():
            commentary.append("Contradiction detected")

        if "unknown action" in run.lower():
            commentary.append("Possible hallucinated action")

    return list(set(commentary))