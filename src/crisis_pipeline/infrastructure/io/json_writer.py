import json


class JSONWriter:
    def write(self, file_path: str, data: dict):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)