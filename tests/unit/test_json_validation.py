import dataclasses
import importlib
import inspect
from typing import Any, Dict, Tuple, Type

import pytest


def _is_pydantic_model(cls: type) -> bool:
    return hasattr(cls, "model_fields") or hasattr(cls, "__fields__")


def _is_dataclass_type(cls: type) -> bool:
    return inspect.isclass(cls) and dataclasses.is_dataclass(cls)


def _candidate_contract_classes(module):
    preferred_names = [
        "NewsEvent",
        "ExtractedEvent",
        "ExtractionResult",
        "EventContract",
        "ExtractionContract",
    ]

    classes = []
    for name in preferred_names:
        cls = getattr(module, name, None)
        if inspect.isclass(cls):
            classes.append(cls)

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj not in classes:
            classes.append(obj)

    return classes


def _build_placeholder_value(field_name: str, annotation: Any):
    name = field_name.lower()

    if annotation in [int]:
        return 1
    if annotation in [float]:
        return 0.95
    if annotation in [bool]:
        return True
    if annotation in [list]:
        return []
    if annotation in [dict]:
        return {}
    if annotation in [str]:
        if "date" in name:
            return "2026-04-15"
        if "time" in name:
            return "10:30"
        if "severity" in name:
            return "high"
        if "location" in name:
            return "Galle"
        if "event" in name:
            return "Flood warning"
        if "source" in name:
            return "news_feed.txt"
        return "sample_text"

    # fallback for Optional/Union/unknown types
    return "sample_text"


def _build_valid_payload_from_model(model_cls: Type) -> Dict[str, Any]:
    payload = {}

    if hasattr(model_cls, "model_fields"):  # Pydantic v2
        fields = model_cls.model_fields
        for name, field in fields.items():
            if field.is_required():
                payload[name] = _build_placeholder_value(name, field.annotation)
        return payload

    if hasattr(model_cls, "__fields__"):  # Pydantic v1
        fields = model_cls.__fields__
        for name, field in fields.items():
            if field.required:
                payload[name] = _build_placeholder_value(name, getattr(field, "type_", str))
        return payload

    if _is_dataclass_type(model_cls):
        for field in dataclasses.fields(model_cls):
            if field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING:
                payload[field.name] = _build_placeholder_value(field.name, field.type)
        return payload

    annotations = getattr(model_cls, "__annotations__", {})
    for name, annotation in annotations.items():
        payload[name] = _build_placeholder_value(name, annotation)
    return payload


def _resolve_validation_target() -> Tuple[str, Any]:
    """
    Resolution order:
    1. validator function in domain.validators
    2. contract model in domain.contracts
    """
    validators_module = importlib.import_module("crisis_pipeline.domain.validators")
    contracts_module = importlib.import_module("crisis_pipeline.domain.contracts")

    candidate_validator_names = [
        "validate_extraction_json",
        "validate_json_model",
        "validate_event_json",
        "validate_news_event",
        "validate",
    ]

    for name in candidate_validator_names:
        fn = getattr(validators_module, name, None)
        if callable(fn):
            return ("validator", fn)

    for cls in _candidate_contract_classes(contracts_module):
        if _is_pydantic_model(cls) or _is_dataclass_type(cls) or hasattr(cls, "__annotations__"):
            return ("model", cls)

    raise AssertionError(
        "No JSON validator function or contract model found. "
        "Expose one in crisis_pipeline.domain.validators or crisis_pipeline.domain.contracts."
    )


def _validate_payload(target_kind: str, target: Any, payload: Dict[str, Any]):
    if target_kind == "validator":
        return target(payload)

    if target_kind == "model":
        if hasattr(target, "model_validate"):  # Pydantic v2
            return target.model_validate(payload)
        return target(**payload)

    raise AssertionError("Unsupported validation target")


def test_valid_json_payload_should_pass_validation():
    target_kind, target = _resolve_validation_target()

    if target_kind == "model":
        payload = _build_valid_payload_from_model(target)
    else:
        # fallback payload for validator-only style
        payload = {
            "event": "Flood warning",
            "location": "Galle",
            "severity": "high",
            "date": "2026-04-15",
        }

    result = _validate_payload(target_kind, target, payload)

    assert result is not None


def test_missing_required_field_should_fail_validation():
    target_kind, target = _resolve_validation_target()

    if target_kind == "model":
        payload = _build_valid_payload_from_model(target)
        if not payload:
            pytest.skip("Model has no detectable required fields to test")
        first_required_key = next(iter(payload.keys()))
        payload.pop(first_required_key)
    else:
        payload = {
            "location": "Galle",
            "severity": "high",
            "date": "2026-04-15",
        }

    with pytest.raises(Exception):
        _validate_payload(target_kind, target, payload)