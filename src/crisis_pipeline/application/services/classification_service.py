from crisis_pipeline.infrastructure.llm.model_gateway import ModelGateway
from crisis_pipeline.infrastructure.llm.prompt_loader import load_prompt
from crisis_pipeline.infrastructure.parsing.response_parser import parse_classification

class ClassificationService:
    def __init__(self):
        self.model = ModelGateway()
        self.prompt_template = load_prompt("prompts/classification/few_shot_classifier.txt")

    def classify(self, message: str) -> dict:
        prompt = self.prompt_template.replace("{{message}}", message)

        raw_output = self.model.generate(prompt)

        parsed = parse_classification(raw_output)

        return parsed
