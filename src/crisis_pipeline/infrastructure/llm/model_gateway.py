from __future__ import annotations

import time
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from crisis_pipeline.infrastructure.io.file_manager import FileManager
from crisis_pipeline.infrastructure.logging.logger import LoggerFactory


load_dotenv()

DEFAULT_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
)


class LLMGateway:
    """
    Industrial LLM Gateway with:
    - retry + fallback models
    - raw response storage
    - structured logging
    - execution metadata
    """

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

        self.client = genai.Client(api_key=api_key)

        configured_model = config.get("model") or os.getenv("GEMINI_MODEL")
        self.model_name = configured_model or DEFAULT_MODELS[0]
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 512)
        self.retry_attempts = config.get("retries", 3)
        self.timeout = config.get("timeout", 10)

        # fallback model strategy
        fallback_models = [self.model_name]
        for model_name in DEFAULT_MODELS:
            if model_name not in fallback_models:
                fallback_models.append(model_name)

        self.model_names = fallback_models

        # 🔹 OLD LOGGER (kept for compatibility)
        self.logger = logging.getLogger("llm_calls")

        # 🔹 NEW INDUSTRIAL COMPONENTS
        self.file_manager = FileManager()
        logger_factory = LoggerFactory()

        self.app_logger = logger_factory.get_app_logger()
        self.llm_logger = logger_factory.get_llm_logger()
        self.warning_logger = logger_factory.get_warning_logger()
        self.logger_factory = logger_factory

    # =========================================================
    # 🔹 CORE GENERATE FUNCTION (UPGRADED)
    # =========================================================

    def generate(
        self,
        prompt: str,
        module_name: str,
        input_file: str,
        output_file: str,
        response_mime_type: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        started_at = self.file_manager.timestamp()
        stamp = self.file_manager.timestamp_slug()

        raw_output_dir = "outputs/artifacts/raw_llm_outputs"
        raw_output_file = f"{raw_output_dir}/{module_name}_{stamp}.txt"

        last_error = "unknown error"

        for model_name in self.model_names:
            for attempt in range(self.retry_attempts):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens,
                            response_mime_type=response_mime_type,
                            response_schema=response_schema,
                        ),
                    )

                    text = response.text
                    self.model_name = model_name

                    # 🔹 STORE RAW OUTPUT
                    self.file_manager.write_text(raw_output_file, text)

                    finished_at = self.file_manager.timestamp()

                    # 🔹 STRUCTURED LOG (LLM AUDIT)
                    log_payload = {
                        "event": "llm_call",
                        "module_name": module_name,
                        "timestamp": finished_at,
                        "model_used": model_name,
                        "temperature_used": self.temperature,
                        "input_file_name": input_file,
                        "output_file_name": output_file,
                        "raw_response_file": raw_output_file,
                        "prompt_length": len(prompt),
                    }

                    self.logger_factory.log_llm_call(self.llm_logger, log_payload)

                    # 🔹 APP LOG
                    self.app_logger.info(
                        f"LLM SUCCESS | module={module_name} | model={model_name} | input={input_file}"
                    )

                    return {
                        "raw_response": text,
                        "raw_response_file": raw_output_file,
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "model_used": model_name,
                        "temperature_used": self.temperature,
                        "input_file_name": input_file,
                        "output_file_name": output_file,
                    }

                except Exception as e:
                    error_text = str(e)
                    last_error = error_text

                    # 🔹 WARNING LOG
                    self.warning_logger.warning(
                        f"LLM FAIL | module={module_name} | model={model_name} | attempt={attempt+1} | error={error_text}"
                    )

                    unsupported_model = (
                        "not found" in error_text.lower()
                        or "not supported for generatecontent" in error_text.lower()
                    )

                    if unsupported_model:
                        break

                    time.sleep(2)

        # 🔴 FINAL FAILURE
        self.app_logger.error(
            f"LLM completely failed | module={module_name} | input={input_file}"
        )

        raise RuntimeError(f"LLM failed after retries: {last_error}")


# backward compatibility
ModelGateway = LLMGateway
