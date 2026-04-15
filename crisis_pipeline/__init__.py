"""Compatibility package for local development without installation."""

from pathlib import Path


_SRC_PACKAGE_DIR = Path(__file__).resolve().parent.parent / "src" / "crisis_pipeline"

if not _SRC_PACKAGE_DIR.is_dir():
    raise ImportError(f"Expected package directory at {_SRC_PACKAGE_DIR}")

__path__ = [str(_SRC_PACKAGE_DIR)]
