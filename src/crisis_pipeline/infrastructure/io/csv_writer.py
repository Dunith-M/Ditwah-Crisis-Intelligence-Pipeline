import csv


class CSVWriter:
    def write(self, file_path: str, data: list, headers: list):
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)