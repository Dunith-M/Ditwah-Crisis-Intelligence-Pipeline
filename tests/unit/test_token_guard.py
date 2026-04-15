import pytest

from crisis_pipeline.application.services.token_service import TokenService


def test_process_allows_text_within_limit(monkeypatch):
    service = TokenService(max_tokens=150)

    monkeypatch.setattr(service.counter, "count", lambda text: 120)

    result = service.process("normal sized input")

    assert result["tokens"] == 120
    assert result["action"] == "allowed"
    assert result["processed_text"] == "normal sized input"
    assert result["original_text"] == "normal sized input"


def test_process_blocks_text_when_far_above_limit(monkeypatch):
    service = TokenService(max_tokens=150)

    monkeypatch.setattr(service.counter, "count", lambda text: 400)

    result = service.process("very large input")

    assert result["tokens"] == 400
    assert result["action"] == "blocked"
    assert result["processed_text"] == ""
    assert result["original_text"] == "very large input"


def test_process_summarizes_text_when_moderately_above_limit(monkeypatch):
    service = TokenService(max_tokens=150)

    monkeypatch.setattr(service.counter, "count", lambda text: 220)
    monkeypatch.setattr(service, "summarize", lambda text: "short summary")

    result = service.process("moderately large input")

    assert result["tokens"] == 220
    assert result["action"] == "summarized"
    assert result["processed_text"] == "short summary"
    assert result["original_text"] == "moderately large input"