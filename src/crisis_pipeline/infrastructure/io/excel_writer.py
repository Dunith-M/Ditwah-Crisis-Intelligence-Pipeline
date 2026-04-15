import pandas as pd
from pathlib import Path


class ExcelWriter:
    def write(self, file_path: str, data: list):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)


def save_excel(data, file_path: str):
    if isinstance(data, pd.DataFrame):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        data.to_excel(file_path, index=False)
        return

    ExcelWriter().write(file_path, data)
