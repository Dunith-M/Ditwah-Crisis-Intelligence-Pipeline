from typing import List, Dict
from pathlib import Path
from crisis_pipeline.application.services.reasoning_service import ReasoningService
from crisis_pipeline.infrastructure.parsing.response_parser import ResponseParser


class ScoreIncidentsUseCase:

    def __init__(self):
        self.reasoning_service = ReasoningService()
        self.parser = ResponseParser()

    def execute(self, incidents: List[str]) -> List[Dict]:
        results = []

        for incident in incidents:
            raw_output = self.reasoning_service.score_incident(incident)
            try:
                parsed = self.parser.parse_json(raw_output)
            except ValueError:
                debug_path = Path("outputs/debug/last_score_incident_raw_output.txt")
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                debug_path.write_text(raw_output, encoding="utf-8")
                raise

            parsed["incident_text"] = incident
            results.append(parsed)

        return results
