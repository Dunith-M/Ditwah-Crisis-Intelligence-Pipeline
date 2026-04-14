import pandas as pd
from crisis_pipeline.infrastructure.io.text_loader import load_lines
from crisis_pipeline.application.services.classification_service import ClassificationService

def run_classification(input_path: str) -> pd.DataFrame:
    messages = load_lines(input_path)

    service = ClassificationService()

    results = []

    for msg in messages:
        output = service.classify(msg)

        results.append({
            "message": msg,
            "district": output.get("district"),
            "intent": output.get("intent"),
            "priority": output.get("priority")
        })

    df = pd.DataFrame(results)

    return df