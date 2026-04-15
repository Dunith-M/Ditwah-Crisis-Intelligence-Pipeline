from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any


class FileManager:
    def ensure_dir(self, path: str | Path) -> Path:
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_text(self, file_path: str | Path, content: str) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, file_path: str | Path, data: Any, indent: int = 2) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return path

    def append_text(self, file_path: str | Path, content: str) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return path

    def timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def timestamp_slug(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")