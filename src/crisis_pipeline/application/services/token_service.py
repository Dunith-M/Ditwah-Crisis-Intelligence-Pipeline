from typing import Dict
from infrastructure.token.counter import TokenCounter


class TokenService:

    def __init__(self, max_tokens: int = 150):
        self.counter = TokenCounter()
        self.max_tokens = max_tokens

    def process(self, text: str) -> Dict:
        token_count = self.counter.count(text)

        result = {
            "original_text": text,
            "processed_text": text,
            "tokens": token_count,
            "action": "allowed"
        }

        # ✅ within limit → allow
        if token_count <= self.max_tokens:
            return result

        # --- decision logic ---
        if token_count > self.max_tokens * 2:
            # 🔴 very large → block
            result["processed_text"] = ""
            result["action"] = "blocked"

        else:
            # 🟡 moderate → summarize (instead of truncate)
            summarized = self.summarize(text)
            result["processed_text"] = summarized
            result["action"] = "summarized"

        return result

    def summarize(self, text: str) -> str:
        """
        Simple fallback summarization.
        In real system → call LLM using prompt.
        """
        return text[:100] + "..." if len(text) > 100 else text