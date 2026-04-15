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

    def load_lines(self, file_path: str) -> List[str]:
        return self.load(file_path)


def load_lines(file_path: str, encoding: str = "utf-8") -> List[str]:
    return TextLoader(encoding=encoding).load(file_path)
