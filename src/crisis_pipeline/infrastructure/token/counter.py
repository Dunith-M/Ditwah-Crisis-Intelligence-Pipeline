from typing import List


class TokenCounter:
    """
    Simple token estimator.
    Rule: 1 token ≈ 4 characters (rough approximation)
    """

    def count(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def batch_count(self, texts: List[str]) -> List[int]:
        return [self.count(t) for t in texts]