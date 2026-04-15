import json
from pathlib import Path


class JSONWriter:
    def write(self, file_path: str, data: dict):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


JsonWriter = JSONWriter
