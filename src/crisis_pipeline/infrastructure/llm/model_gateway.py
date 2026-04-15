import time
import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()

DEFAULT_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)


class LLMGateway:
    def __init__(self, config: dict | None = None):
        config = config or {}
        api_key = (
            config.get("api_key")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "Missing Gemini API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in your environment or .env file."
            )

        genai.configure(api_key=api_key)

        configured_model = config.get("model") or os.getenv("GEMINI_MODEL")
        self.model_name = configured_model or DEFAULT_MODELS[0]
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 512)
        self.retry_attempts = config.get("retries", 3)
        self.timeout = config.get("timeout", 10)

        fallback_models = [self.model_name]
        for model_name in DEFAULT_MODELS:
            if model_name not in fallback_models:
                fallback_models.append(model_name)

        self.model_names = fallback_models
        self.model = genai.GenerativeModel(self.model_name)
        self.logger = logging.getLogger("llm_calls")

    def generate(self, prompt: str) -> str:
        for model_name in self.model_names:
            self.model = genai.GenerativeModel(model_name)

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
                    self.model_name = model_name

                    self.logger.info(
                        f"LLM SUCCESS | Model: {model_name} | Prompt length: {len(prompt)}"
                    )

                    return text

                except Exception as e:
                    error_text = str(e)
                    self.logger.warning(
                        f"LLM FAIL | Model: {model_name} | Attempt {attempt+1}: {error_text}"
                    )

                    unsupported_model = (
                        "not found" in error_text.lower()
                        or "not supported for generatecontent" in error_text.lower()
                    )
                    if unsupported_model:
                        break

                    time.sleep(2)

        raise RuntimeError("LLM failed after retries")


ModelGateway = LLMGateway
