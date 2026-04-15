from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional


# =========================================================
#  SIMPLE LOGGER (Backward Compatibility)
# =========================================================

def get_logger(name: str = "crisis_pipeline.app") -> logging.Logger:
    """
    Simple logger getter (used in legacy code).
    Now enhanced to ensure logs go to app.log.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_dir = Path("outputs/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger


def log_token_event(record: dict):
    """
    Logs token-related warnings.
    Now writes into warnings.log instead of generic logger.
    """
    factory = LoggerFactory()
    logger = factory.get_warning_logger()

    if record["action"] != "allowed":
        logger.warning(
            f'Token issue | action={record["action"]} | tokens={record["tokens"]}'
        )


# =========================================================
# 🔹 INDUSTRIAL LOGGER FACTORY (NEW)
# =========================================================

class LoggerFactory:
    """
    Centralized logging system.

    Provides:
    - App logs
    - Warning logs (invalid JSON, parsing issues, etc.)
    - LLM audit logs (structured JSON logs)
    """

    def __init__(self, log_dir: str = "outputs/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.app_log_file = self.log_dir / "app.log"
        self.warning_log_file = self.log_dir / "warnings.log"
        self.llm_log_file = self.log_dir / "llm_calls.log"

    def _build_logger(
        self,
        name: str,
        file_path: Path,
        level: int = logging.INFO,
        formatter: Optional[logging.Formatter] = None,
    ) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        handler = logging.FileHandler(file_path, encoding="utf-8")
        handler.setLevel(level)

        if formatter is None:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    # -----------------------------------------------------

    def get_app_logger(self) -> logging.Logger:
        return self._build_logger(
            name="crisis_pipeline.app",
            file_path=self.app_log_file,
            level=logging.INFO,
        )

    def get_warning_logger(self) -> logging.Logger:
        return self._build_logger(
            name="crisis_pipeline.warnings",
            file_path=self.warning_log_file,
            level=logging.WARNING,
        )

    def get_llm_logger(self) -> logging.Logger:
        """
        LLM logs are JSON structured (important for audit).
        """
        json_formatter = logging.Formatter("%(message)s")

        return self._build_logger(
            name="crisis_pipeline.llm",
            file_path=self.llm_log_file,
            level=logging.INFO,
            formatter=json_formatter,
        )

    # -----------------------------------------------------

    def log_llm_call(self, logger: logging.Logger, payload: dict) -> None:
        """
        Stores structured LLM metadata as JSON.
        """
        logger.info(json.dumps(payload, ensure_ascii=False))
