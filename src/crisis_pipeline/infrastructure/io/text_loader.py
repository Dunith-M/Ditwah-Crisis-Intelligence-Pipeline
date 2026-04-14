from pathlib import Path
from typing import List


class TextLoader:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def load(self, file_path: str) -> List[str]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding=self.encoding) as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        return lines