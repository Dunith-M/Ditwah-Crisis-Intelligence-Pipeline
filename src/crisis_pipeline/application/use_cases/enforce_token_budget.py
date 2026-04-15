from typing import List
from application.services.token_service import TokenService


class EnforceTokenBudgetUseCase:

    def __init__(self):
        self.token_service = TokenService()

    def execute(self, messages: List[str]) -> List[dict]:
        results = []

        for msg in messages:
            result = self.token_service.process(msg)
            results.append(result)

        return results