# Copyright 2022 Alex Butler
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import os
import typing as t
from enum import Enum
from functools import wraps

from dbt_feature_flags import base, fme, harness, launchdarkly


class _MockClient:
    pass


_MOCK_CLIENT: t.Final = _MockClient()


class SupportedProviders(str, Enum):
    Harness = "harness"
    FME = "fme"
    LaunchDarkly = "launchdarkly"
    NoopClient = "mock"


def _is_truthy(value: str) -> bool:
    """Return True if the value is truthy, False otherwise."""
    return value.lower() in ("1", "true", "yes")


def _get_client() -> base.BaseFeatureFlagsClient | _MockClient:
    """Return the user specified client.

    Valid implementations MUST inherit from BaseFeatureFlagsClient.
    """
    provider_name = os.getenv("DBT_FF_PROVIDER")

    if _is_truthy(os.getenv("DBT_FF_DISABLE", "0")):
        return _MOCK_CLIENT

    if not provider_name:
        return _MOCK_CLIENT

    try:
        provider = SupportedProviders(provider_name)
    except ValueError as exc:
        raise RuntimeError(
            f"Unsupported dbt feature flag provider: DBT_FF_PROVIDER={provider_name}"
        ) from exc

    if provider == SupportedProviders.Harness:
        return harness.HarnessFeatureFlagsClient()
    if provider == SupportedProviders.FME:
        return fme.HarnessFMEClient()
    if provider == SupportedProviders.LaunchDarkly:
        return launchdarkly.LaunchDarklyFeatureFlagsClient()

    return _MOCK_CLIENT


def get_rendered(
    fn: t.Callable[..., t.Any],
    client: base.BaseFeatureFlagsClient | _MockClient,
) -> t.Callable[..., t.Any]:
    """Patch dbt's jinja environment to include feature flag functions."""

    if getattr(fn, "status", None) == "patched":
        return fn

    @wraps(fn)
    def _wrapped(
        string: str,
        ctx: dict[str, t.Any],
        node: t.Any = None,
        capture_macros: bool = False,
        native: bool = False,
    ) -> t.Any:
        if client is _MOCK_CLIENT:
            ctx["feature_flag"] = ctx.get("var", lambda _, default=False: default)
            ctx["feature_flag_str"] = ctx.get("var", lambda _, default="": default)
            ctx["feature_flag_num"] = ctx.get("var", lambda _, default=0: default)
            ctx["feature_flag_json"] = ctx.get(
                "var", lambda _, default=None: {} if default is None else default
            )
        else:
            feature_client = t.cast(base.BaseFeatureFlagsClient, client)
            ctx["feature_flag"] = feature_client.bool_variation
            ctx["feature_flag_str"] = feature_client.string_variation
            ctx["feature_flag_num"] = feature_client.number_variation
            ctx["feature_flag_json"] = feature_client.json_variation
        return fn(string, ctx, node, capture_macros, native)

    setattr(_wrapped, "status", "patched")
    return _wrapped


def patch_dbt_environment() -> None:
    """Patch dbt's jinja environment to include feature flag functions."""
    from dbt.clients import jinja

    original_get_rendered = getattr(jinja, "_get_rendered", jinja.get_rendered)
    setattr(jinja, "_get_rendered", original_get_rendered)
    setattr(jinja, "get_rendered", get_rendered(original_get_rendered, _get_client()))


if __name__ == "__main__":
    patch_dbt_environment()
