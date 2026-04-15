from crisis_pipeline.application.use_cases.enforce_token_budget import EnforceTokenBudgetUseCase
from crisis_pipeline.infrastructure.io.text_loader import TextLoader
from crisis_pipeline.infrastructure.io.json_writer import JsonWriter
from crisis_pipeline.application.services.reporting_service import generate_token_report
from crisis_pipeline.infrastructure.logging.logger import log_token_event


def run():
    loader = TextLoader()
    messages = loader.load("data/raw/sample_messages.txt")

    use_case = EnforceTokenBudgetUseCase()
    results = use_case.execute(messages)

    for r in results:
        log_token_event(r)

    report = generate_token_report(results)

    writer = JsonWriter()
    writer.write("outputs/reports/token_guard_report.md", report)


if __name__ == "__main__":
    run()
