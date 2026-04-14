import time
import logging
import google.generativeai as genai


class LLMGateway:
    def __init__(self, config: dict):
        genai.configure(api_key=config["api_key"])

        self.model_name = config["model"]
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 512)
        self.retry_attempts = config.get("retries", 3)
        self.timeout = config.get("timeout", 10)

        self.model = genai.GenerativeModel(self.model_name)
        self.logger = logging.getLogger("llm_calls")

    def generate(self, prompt: str) -> str:
        for attempt in range(self.retry_attempts):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens,
                    }
                )

                text = response.text

                self.logger.info(f"LLM SUCCESS | Tokens ~ | Prompt length: {len(prompt)}")

                return text

            except Exception as e:
                self.logger.warning(f"LLM FAIL (attempt {attempt+1}): {str(e)}")
                time.sleep(2)

        raise RuntimeError("LLM failed after retries")