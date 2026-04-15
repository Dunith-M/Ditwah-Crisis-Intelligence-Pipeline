"""Project-local Python startup customizations.

Ensures the repository's ``src`` directory is importable when running modules
directly from the project root without installing the package first.
"""

from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parent / "src"

if SRC_DIR.is_dir():
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
