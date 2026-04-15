from pathlib import Path


class PromptLoader:
    def __init__(self, base_path: str = "prompts"):
        self.base_path = Path(base_path)

    def load(self, relative_path: str) -> str:
        file_path = self.base_path / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt not found: {file_path}")

        return file_path.read_text(encoding="utf-8")


def load_prompt(relative_path: str, base_path: str = "prompts") -> str:
    normalized_path = relative_path
    if relative_path.startswith(f"{base_path}/"):
        normalized_path = relative_path[len(base_path) + 1:]

    return PromptLoader(base_path=base_path).load(normalized_path)
