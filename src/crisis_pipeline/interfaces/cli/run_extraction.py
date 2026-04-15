from crisis_pipeline.application.use_cases.extract_news_events import ExtractNewsEventsUseCase
from crisis_pipeline.shared.paths import Paths


def main():
    use_case = ExtractNewsEventsUseCase()

    use_case.execute(
        input_path=Paths.NEWS_FEED,
        output_path=Paths.FLOOD_REPORT
    )


if __name__ == "__main__":
    main()