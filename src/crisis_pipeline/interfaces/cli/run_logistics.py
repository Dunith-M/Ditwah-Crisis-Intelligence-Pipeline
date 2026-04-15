from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from crisis_pipeline.infrastructure.io.text_loader import TextLoader
from crisis_pipeline.application.use_cases.score_incidents import ScoreIncidentsUseCase
from crisis_pipeline.application.use_cases.choose_rescue_route import ChooseRescueRouteUseCase
from crisis_pipeline.infrastructure.io.json_writer import JsonWriter


def main():

    loader = TextLoader()
    incidents = loader.load_lines("data/raw/incidents.txt")

    scorer = ScoreIncidentsUseCase()
    scored = scorer.execute(incidents)

    router = ChooseRescueRouteUseCase()
    decision = router.execute(scored)

    writer = JsonWriter()
    writer.write("data/processed/route_decision.json", decision)


if __name__ == "__main__":
    main()
