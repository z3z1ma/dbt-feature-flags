import json
import pathlib
from types import SimpleNamespace
import typing as t

import pytest

from dbt_feature_flags.base import JSONValue, BaseFeatureFlagsClient
from dbt_feature_flags.patch import _MOCK_CLIENT, _get_client, _is_truthy
from dbt_feature_flags.patch import patch_dbt_environment

patch_dbt_environment()


def feature_flag_template(
    condition: str,
    true_select: str = "select 100 as valid",
    false_select: str = "select -100 as invalid",
) -> str:
    return f"""
    {{%- set test_case -%}}
        {{%- if {condition} -%}}
            {true_select}
        {{%- else -%}}
            {false_select}
        {{%- endif -%}}
    {{%- endset -%}}
    {{{{- test_case | trim -}}}}
    """


@pytest.mark.parametrize(
    ("condition", "context", "expected", "true_select", "false_select"),
    [
        (
            'feature_flag("Test_Flag", default=False)',
            {},
            "select -100 as valid",
            "select 100 as invalid",
            "select -100 as valid",
        ),
        (
            'feature_flag("Test_Flag", default=True)',
            {},
            "select 100 as valid",
            None,
            None,
        ),
        (
            'feature_flag("Test_Flag", default=feature_flag("Nested_Flag", default=True))',
            {},
            "select 100 as valid",
            None,
            None,
        ),
        (
            'feature_flag("Test_Flag", default=var("Dbt_Var", default=True))',
            {},
            "select 100 as valid",
            None,
            None,
        ),
        (
            'feature_flag("Test_Flag", default=var("Dbt_Var", default=True))',
            {"Dbt_Var": False},
            "select -100 as valid",
            "select 100 as invalid",
            "select -100 as valid",
        ),
    ],
)
def test_mock_feature_flag_rendering(
    condition: str,
    context: dict[str, t.Any],
    expected: str,
    true_select: str | None,
    false_select: str | None,
) -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    template = feature_flag_template(
        condition,
        true_select or "select 100 as valid",
        false_select or "select -100 as invalid",
    )

    assert get_rendered(template, generate_base_context(context)) == expected


def test_get_client_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBT_FF_DISABLE", raising=False)
    monkeypatch.delenv("DBT_FF_PROVIDER", raising=False)

    assert _get_client() is _MOCK_CLIENT


def test_get_client_disable_overrides_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DBT_FF_DISABLE", "true")
    monkeypatch.setenv("DBT_FF_PROVIDER", "not-a-provider")

    assert _get_client() is _MOCK_CLIENT


def test_get_client_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBT_FF_DISABLE", raising=False)
    monkeypatch.setenv("DBT_FF_PROVIDER", "not-a-provider")

    with pytest.raises(RuntimeError, match="Unsupported dbt feature flag provider"):
        _get_client()


@pytest.mark.parametrize(
    ("provider", "module_name", "class_name"),
    [
        ("harness", "harness", "HarnessFeatureFlagsClient"),
        ("fme", "fme", "HarnessFMEClient"),
        ("launchdarkly", "launchdarkly", "LaunchDarklyFeatureFlagsClient"),
    ],
)
def test_get_client_constructs_configured_provider(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    module_name: str,
    class_name: str,
) -> None:
    from dbt_feature_flags import patch

    client = StaticClient()
    monkeypatch.delenv("DBT_FF_DISABLE", raising=False)
    monkeypatch.setenv("DBT_FF_PROVIDER", provider)
    monkeypatch.setattr(getattr(patch, module_name), class_name, lambda: client)

    assert patch._get_client() is client


def test_truthy_env_parser() -> None:
    assert _is_truthy("1")
    assert _is_truthy("TRUE")
    assert _is_truthy("yes")
    assert not _is_truthy("0")
    assert not _is_truthy("false")


class StaticClient(BaseFeatureFlagsClient):
    def bool_variation(self, flag: str, default: bool = False) -> bool:
        return default

    def string_variation(self, flag: str, default: str = "") -> str:
        return default

    def number_variation(self, flag: str, default: float | int = 0) -> float | int:
        return default

    def json_variation(self, flag: str, default: JSONValue | None = None) -> JSONValue:
        return {} if default is None else default


class BadBoolClient(StaticClient):
    def bool_variation(self, flag: str, default: bool = False) -> bool:
        return t.cast(bool, "not a bool")


class BadJSONClient(StaticClient):
    def json_variation(self, flag: str, default: JSONValue | None = None) -> JSONValue:
        return t.cast(JSONValue, None)


def test_client_validator_accepts_json_default_none() -> None:
    client = StaticClient()

    assert client.json_variation("json-flag") == {}
    assert client.json_variation("json-flag", []) == []


def test_client_validator_rejects_wrong_default_type() -> None:
    client = StaticClient()

    with pytest.raises(ValueError, match="Invalid default value"):
        client.bool_variation("bool-flag", t.cast(bool, "true"))


def test_client_validator_rejects_wrong_return_type() -> None:
    client = BadBoolClient()

    with pytest.raises(ValueError, match="Invalid feature flag evaluation"):
        client.bool_variation("bool-flag")


def test_client_validator_rejects_json_none_return() -> None:
    client = BadJSONClient()

    with pytest.raises(ValueError, match="Invalid feature flag evaluation"):
        client.json_variation("json-flag")


class FakeClient(StaticClient):
    def __init__(self, values: dict[str, bool]) -> None:
        self.values = values
        self.shutdown_called = False
        super().__init__()

    def bool_variation(self, flag: str, default: bool = False) -> bool:
        return self.values.get(flag, default)

    def shutdown(self) -> None:
        self.shutdown_called = True


def prepare_preflight_target(
    tmp_path: pathlib.Path, previous: bool
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    cache_file = target_dir / ".fme_flag_state.json"
    partial_parse = target_dir / "partial_parse.msgpack"
    cache_file.write_text(json.dumps({"flag": previous}))
    partial_parse.write_bytes(b"cached")
    return target_dir, cache_file, partial_parse


def test_preflight_skips_mock_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    from dbt_feature_flags import patch, preflight

    target_dir = tmp_path / "target"
    monkeypatch.setattr(patch, "_get_client", lambda: patch._MOCK_CLIENT)

    preflight.run(["flag"], target_dir=str(target_dir))

    assert not target_dir.exists()


def test_preflight_invalidates_partial_parse_when_flags_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    from dbt_feature_flags import patch, preflight

    target_dir, cache_file, partial_parse = prepare_preflight_target(
        tmp_path, previous=False
    )
    client = FakeClient({"flag": True})
    monkeypatch.setattr(patch, "_get_client", lambda: client)

    preflight.run(["flag"], target_dir=str(target_dir))

    assert not partial_parse.exists()
    assert json.loads(cache_file.read_text()) == {"flag": True}
    assert client.shutdown_called


def test_preflight_keeps_partial_parse_when_flags_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    from dbt_feature_flags import patch, preflight

    target_dir, cache_file, partial_parse = prepare_preflight_target(
        tmp_path, previous=True
    )
    client = FakeClient({"flag": True})
    monkeypatch.setattr(patch, "_get_client", lambda: client)

    preflight.run(["flag"], target_dir=str(target_dir))

    assert partial_parse.exists()
    assert json.loads(cache_file.read_text()) == {"flag": True}
    assert client.shutdown_called


class FakeHarnessSDK:
    def bool_variation(self, flag: str, target: object, default: bool) -> bool:
        return not default

    def string_variation(self, flag: str, target: object, default: str) -> str:
        return f"{flag}:{default}"

    def number_variation(
        self, flag: str, target: object, default: float | int
    ) -> float | int:
        return default + 1

    def json_variation(
        self, flag: str, target: object, default: JSONValue
    ) -> JSONValue:
        return {"flag": flag, "default": default}


def test_harness_provider_delegates_to_sdk_client() -> None:
    from dbt_feature_flags.harness import HarnessFeatureFlagsClient

    client = object.__new__(HarnessFeatureFlagsClient)
    client.client = FakeHarnessSDK()
    client.target = object()
    BaseFeatureFlagsClient.__init__(client)

    assert client.bool_variation("enabled", False)
    assert client.string_variation("name", "fallback") == "name:fallback"
    assert client.number_variation("count", 1) == 2
    assert client.json_variation("payload", {"x": 1}) == {
        "flag": "payload",
        "default": {"x": 1},
    }


class FakeLaunchDarklySDK:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, t.Any]] = []

    def variation(self, flag: str, target: object, default: t.Any) -> t.Any:
        self.calls.append((flag, target, default))
        return default


def test_launchdarkly_provider_uses_context_positional_argument() -> None:
    from dbt_feature_flags.launchdarkly import LaunchDarklyFeatureFlagsClient

    client = object.__new__(LaunchDarklyFeatureFlagsClient)
    sdk = FakeLaunchDarklySDK()
    client.client = sdk
    client.target = {"key": "dbt-default"}
    BaseFeatureFlagsClient.__init__(client)

    assert client.bool_variation("enabled", False) is False
    assert client.json_variation("payload") == {}
    assert sdk.calls == [
        ("enabled", {"key": "dbt-default"}, False),
        ("payload", {"key": "dbt-default"}, {}),
    ]


class FakeSplitClient:
    def __init__(self) -> None:
        self.treatments = {
            "enabled": "on",
            "disabled": "control",
            "text": "variant",
            "number": "3.5",
            "bad-number": "three",
        }
        self.configs = {
            "payload": SimpleNamespace(treatment="on", config='{"enabled": true}'),
            "bad-json": SimpleNamespace(treatment="on", config="{"),
            "missing": SimpleNamespace(treatment="control", config=None),
        }

    def get_treatment(self, _key: str, flag: str) -> str:
        return self.treatments[flag]

    def get_treatment_with_config(self, _key: str, flag: str) -> SimpleNamespace:
        return self.configs[flag]


def test_fme_provider_maps_split_treatments() -> None:
    from dbt_feature_flags.fme import HarnessFMEClient

    client = object.__new__(HarnessFMEClient)
    client._key = "dbt-default"
    client._client = FakeSplitClient()
    BaseFeatureFlagsClient.__init__(client)

    assert client.bool_variation("enabled") is True
    assert client.bool_variation("disabled", True) is True
    assert client.string_variation("text") == "variant"
    assert client.number_variation("number") == 3.5
    assert client.number_variation("bad-number", 7) == 7
    assert client.json_variation("payload") == {"enabled": True}
    assert client.json_variation("bad-json", []) == []
    assert client.json_variation("missing", []) == []


def test_fme_shutdown_factories_waits_for_destroy() -> None:
    from dbt_feature_flags import fme

    class Factory:
        def __init__(self) -> None:
            self.destroyed = False

        def destroy(self, destroyed_event: t.Any) -> None:
            self.destroyed = True
            destroyed_event.set()

    factory = Factory()
    fme._factory_cache["sdk"] = factory
    try:
        fme._shutdown_factories()
    finally:
        fme._factory_cache.clear()

    assert factory.destroyed
