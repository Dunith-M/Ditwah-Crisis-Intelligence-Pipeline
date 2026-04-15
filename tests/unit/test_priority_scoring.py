import importlib
import inspect
from typing import Any, Callable

import pytest


def _extract_numeric(value: Any) -> float:
    """
    Accepts either:
    - raw numeric
    - dict with score-like fields
    - object with score-like attributes
    """
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, dict):
        for key in ["score", "priority_score", "total_score", "incident_score"]:
            if key in value and isinstance(value[key], (int, float)):
                return float(value[key])

    for attr in ["score", "priority_score", "total_score", "incident_score"]:
        if hasattr(value, attr):
            attr_value = getattr(value, attr)
            if isinstance(attr_value, (int, float)):
                return float(attr_value)

    raise AssertionError(f"Could not extract numeric score from return value: {value!r}")


def _resolve_scoring_callable() -> Callable:
    """
    Tries to find a scoring entrypoint inside:
    crisis_pipeline.domain.scoring_rules
    """
    module = importlib.import_module("crisis_pipeline.domain.scoring_rules")

    candidate_function_names = [
        "score_incident",
        "calculate_priority_score",
        "compute_priority_score",
        "compute_score",
        "score",
    ]

    for name in candidate_function_names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn

    candidate_class_names = [
        "PriorityScorer",
        "IncidentScorer",
        "ScoringRules",
    ]

    candidate_method_names = [
        "score_incident",
        "calculate_priority_score",
        "compute_priority_score",
        "compute_score",
        "score",
    ]

    for class_name in candidate_class_names:
        cls = getattr(module, class_name, None)
        if cls and inspect.isclass(cls):
            instance = cls()
            for method_name in candidate_method_names:
                method = getattr(instance, method_name, None)
                if callable(method):
                    return method

    raise AssertionError(
        "No usable scoring callable found in crisis_pipeline.domain.scoring_rules. "
        "Expose one of: score_incident / calculate_priority_score / compute_priority_score / compute_score / score"
    )


@pytest.fixture
def scoring_callable():
    return _resolve_scoring_callable()


def _call_scoring(fn: Callable, payload: dict) -> float:
    result = fn(payload)
    return _extract_numeric(result)


def test_higher_severity_should_not_score_lower(scoring_callable):
    low = {
        "severity": 1,
        "people_affected": 5,
        "resource_need": 1,
        "time_criticality": 1,
    }
    high = {
        "severity": 5,
        "people_affected": 5,
        "resource_need": 1,
        "time_criticality": 1,
    }

    low_score = _call_scoring(scoring_callable, low)
    high_score = _call_scoring(scoring_callable, high)

    assert high_score >= low_score, "Higher severity should not produce a lower score"


def test_more_people_affected_should_not_score_lower(scoring_callable):
    small = {
        "severity": 3,
        "people_affected": 3,
        "resource_need": 2,
        "time_criticality": 2,
    }
    large = {
        "severity": 3,
        "people_affected": 50,
        "resource_need": 2,
        "time_criticality": 2,
    }

    small_score = _call_scoring(scoring_callable, small)
    large_score = _call_scoring(scoring_callable, large)

    assert large_score >= small_score, "More affected people should not reduce priority score"


def test_more_time_critical_case_should_not_score_lower(scoring_callable):
    normal = {
        "severity": 3,
        "people_affected": 10,
        "resource_need": 2,
        "time_criticality": 1,
    }
    urgent = {
        "severity": 3,
        "people_affected": 10,
        "resource_need": 2,
        "time_criticality": 5,
    }

    normal_score = _call_scoring(scoring_callable, normal)
    urgent_score = _call_scoring(scoring_callable, urgent)

    assert urgent_score >= normal_score, "More time-critical incidents should not score lower"