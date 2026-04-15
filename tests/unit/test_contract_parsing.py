import pytest

from crisis_pipeline.infrastructure.parsing.response_parser import ResponseParser


@pytest.fixture
def parser():
    return ResponseParser()


def test_parse_classification_valid_output(parser):
    text = """
    Label: Critical
    Confidence: 0.92
    """

    result = parser.parse_classification(text)

    assert result["label"] == "Critical"
    assert result["confidence"] == "0.92"


def test_parse_classification_ignores_extra_whitespace_and_lines(parser):
    text = """
        Label:   Rescue Needed

        Confidence:   0.88
        Note: Flood level rising
    """

    result = parser.parse_classification(text)

    assert result["label"] == "Rescue Needed"
    assert result["confidence"] == "0.88"
    assert result["note"] == "Flood level rising"


def test_parse_classification_raises_when_label_missing(parser):
    text = """
    Confidence: 0.75
    Reason: uncertain input
    """

    with pytest.raises(ValueError, match="Invalid classification output"):
        parser.parse_classification(text)