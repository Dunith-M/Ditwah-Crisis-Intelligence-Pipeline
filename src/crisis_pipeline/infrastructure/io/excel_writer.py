import pandas as pd


class ExcelWriter:
    def write(self, file_path: str, data: list):
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)