import pandas as pd
from typing import List

from crisis_pipeline.domain.entities import CrisisEvent
from crisis_pipeline.infrastructure.llm.model_gateway import ModelGateway
from crisis_pipeline.infrastructure.llm.prompt_loader import PromptLoader
from crisis_pipeline.infrastructure.io.text_loader import TextLoader
from crisis_pipeline.infrastructure.io.excel_writer import ExcelWriter
from crisis_pipeline.infrastructure.logging.logger import get_logger
from crisis_pipeline.infrastructure.parsing.json_cleaner import JsonCleaner


class ExtractNewsEventsUseCase:

    def __init__(self):
        self.llm = ModelGateway()
        self.prompt_loader = PromptLoader()
        self.text_loader = TextLoader()
        self.excel_writer = ExcelWriter()
        self.logger = get_logger()
        self.cleaner = JsonCleaner()

    def execute(self, input_path: str, output_path: str):

        lines = self.text_loader.load_lines(input_path)

        prompt_template = self.prompt_loader.load("extraction/json_extract.txt")

        valid_events: List[CrisisEvent] = []

        for idx, line in enumerate(lines):

            try:
                # --- Step 1: Send to LLM ---
                prompt = prompt_template.replace("{text}", line)
                response = self.llm.generate(prompt)

                # --- Step 2: Clean JSON ---
                clean_json = self.cleaner.clean(response)

                # --- Step 3: Validate ---
                event = CrisisEvent(**clean_json)

                valid_events.append(event)

            except Exception as e:
                self.logger.warning(f"[Line {idx}] Skipped invalid row: {e}")
                continue

        # --- Step 4: Convert to DataFrame ---
        df = pd.DataFrame([event.dict() for event in valid_events])

        # --- Step 5: Save Excel ---
        self.excel_writer.write(output_path, df.to_dict(orient="records"))

        self.logger.info(f"Extracted {len(valid_events)} valid events.")