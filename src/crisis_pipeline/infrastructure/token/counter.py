class TokenCounter:
    def __init__(self, avg_chars_per_token: int = 4):
        self.avg_chars_per_token = avg_chars_per_token

    def estimate_tokens(self, text: str) -> int:
        return len(text) // self.avg_chars_per_token

    def is_exceeding(self, text: str, limit: int) -> bool:
        return self.estimate_tokens(text) > limit