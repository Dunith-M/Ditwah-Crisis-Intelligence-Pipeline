import importlib
import inspect
import json
from pathlib import Path

import pytest


FAKE_LLM_JSON = json.dumps(
    [
        {
            "event": "Flood warning issued",
            "location": "Galle",
            "severity": "high",
            "date": "2026-04-15"
        },
        {
            "event": "Road access disrupted",
            "location": "Matara",
            "severity": "medium",
            "date": "2026-04-15"
        }
    ]
)


def _patch_llm_layers(monkeypatch):
    """
    Patch likely LLM entrypoints so the test does not call a real model.
    """
    patch_targets = [
        ("crisis_pipeline.infrastructure.llm.model_gateway", ["generate", "complete", "invoke", "run"]),
        ("crisis_pipeline.infrastructure.llm.client", ["generate", "complete", "invoke", "run"]),
        ("crisis_pipeline.application.services.extraction_service", ["generate", "complete", "invoke", "run"]),
    ]

    for module_name, method_names in patch_targets:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue

        for _, cls in inspect.getmembers(module, inspect.isclass):
            for method_name in method_names:
                if hasattr(cls, method_name):
                    monkeypatch.setattr(cls, method_name, lambda self, *a, **k: FAKE_LLM_JSON, raising=False)

        for method_name in method_names:
            fn = getattr(module, method_name, None)
            if callable(fn):
                monkeypatch.setattr(module, method_name, lambda *a, **k: FAKE_LLM_JSON, raising=False)


def _resolve_extraction_runner():
    module = importlib.import_module("crisis_pipeline.application.use_cases.extract_news_events")

    # direct callable functions
    for fn_name in ["run", "execute", "extract_news_events", "main"]:
        fn = getattr(module, fn_name, None)
        if callable(fn):
            return ("function", fn)

    # use case classes
    for cls_name in ["ExtractNewsEventsUseCase", "ExtractNewsEvents", "NewsExtractionUseCase"]:
        cls = getattr(module, cls_name, None)
        if inspect.isclass(cls):
            return ("class", cls)

    # fallback: any class with execute/run
    for _, cls in inspect.getmembers(module, inspect.isclass):
        for method_name in ["execute", "run"]:
            if hasattr(cls, method_name):
                return ("class", cls)

    raise AssertionError(
        "Could not find extraction pipeline entrypoint in "
        "crisis_pipeline.application.use_cases.extract_news_events"
    )


def _invoke_function(fn, input_path: Path, output_path: Path):
    sig = inspect.signature(fn)
    kwargs = {}

    for name in sig.parameters:
        lname = name.lower()
        if "input" in lname or "news" in lname or "file_path" in lname:
            kwargs[name] = str(input_path)
        elif "output" in lname or "save" in lname or "json_path" in lname:
            kwargs[name] = str(output_path)

    return fn(**kwargs) if kwargs else fn()


def _build_stub_dependency(name: str, input_path: Path, output_path: Path):
    lname = name.lower()

    class TextLoaderStub:
        def load(self, *_args, **_kwargs):
            return [line.strip() for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        def load_lines(self, *_args, **_kwargs):
            return self.load()

    class ExtractionServiceStub:
        def extract(self, *_args, **_kwargs):
            return json.loads(FAKE_LLM_JSON)

        def execute(self, *_args, **_kwargs):
            return json.loads(FAKE_LLM_JSON)

        def run(self, *_args, **_kwargs):
            return json.loads(FAKE_LLM_JSON)

    class JsonWriterStub:
        def write(self, file_path, data):
            Path(file_path).write_text(json.dumps(data, indent=2), encoding="utf-8")

        def save(self, file_path, data):
            self.write(file_path, data)

    if "loader" in lname:
        return TextLoaderStub()
    if "extract" in lname or "service" in lname:
        return ExtractionServiceStub()
    if "writer" in lname:
        return JsonWriterStub()

    return None


def _invoke_class(cls, input_path: Path, output_path: Path):
    init_sig = inspect.signature(cls.__init__)
    init_kwargs = {}

    for name, param in list(init_sig.parameters.items())[1:]:  # skip self
        dep = _build_stub_dependency(name, input_path, output_path)
        if dep is not None:
            init_kwargs[name] = dep

    instance = cls(**init_kwargs) if init_kwargs else cls()

    for method_name in ["execute", "run"]:
        method = getattr(instance, method_name, None)
        if callable(method):
            sig = inspect.signature(method)
            kwargs = {}

            for name in sig.parameters:
                lname = name.lower()
                if "input" in lname or "news" in lname or "file_path" in lname:
                    kwargs[name] = str(input_path)
                elif "output" in lname or "save" in lname or "json_path" in lname:
                    kwargs[name] = str(output_path)

            return method(**kwargs) if kwargs else method()

    raise AssertionError("Resolved class has no callable execute/run method")


def test_end_to_end_extraction_pipeline(tmp_path, monkeypatch):
    input_path = tmp_path / "news_feed.txt"
    output_path = tmp_path / "extracted_events.json"

    input_path.write_text(
        "\n".join(
            [
                "Heavy rain has triggered flood warnings in Galle.",
                "Several roads in Matara are temporarily blocked.",
            ]
        ),
        encoding="utf-8",
    )

    _patch_llm_layers(monkeypatch)

    kind, runner = _resolve_extraction_runner()

    if kind == "function":
        _invoke_function(runner, input_path, output_path)
    else:
        _invoke_class(runner, input_path, output_path)

    # If the real pipeline writes the file, check it directly.
    # If it returns the result instead, the test still expects the file path convention.
    assert output_path.exists(), "Extraction pipeline did not create the output JSON file"

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert isinstance(data, (list, dict))
    if isinstance(data, list):
        assert len(data) > 0
        assert isinstance(data[0], dict)