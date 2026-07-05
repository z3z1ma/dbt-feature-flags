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

"""Harness FME (Feature Management & Experimentation) provider.

An additional provider alongside the existing Harness Feature Flags (HFF)
provider. Both providers coexist — use DBT_FF_PROVIDER=harness for HFF
and DBT_FF_PROVIDER=fme for FME.

Required env var: DBT_FF_API_KEY  (FME server-side SDK key)
Optional env var: DBT_TARGET      (used as the targeting key, e.g. "dev", "prod")
"""

from __future__ import annotations

import atexit
from importlib import import_module
import json
import os
import threading
import typing as t

from dbt_feature_flags.base import JSONValue, BaseFeatureFlagsClient

# Module-level singleton — ensures get_factory is called only once per SDK key,
# avoiding the splitio "multiple factory instances" warning.
_factory_cache: dict[str, t.Any] = {}


def _shutdown_factories() -> None:
    """Flush impressions and cleanly shut down all SDK factory instances on exit.

    Passes a threading.Event to destroy() and waits for it — this ensures the
    SDK flushes all queued impressions to Harness before the process exits.
    Without this, destroy() fires asynchronously and impressions are dropped.
    """
    for factory in _factory_cache.values():
        done = threading.Event()
        factory.destroy(destroyed_event=done)
        done.wait(timeout=5)


atexit.register(_shutdown_factories)


class HarnessFMEClient(BaseFeatureFlagsClient):
    def __init__(self) -> None:
        get_factory = import_module("splitio").get_factory
        sdk_key = os.environ.get("DBT_FF_API_KEY")
        if sdk_key is None:
            raise RuntimeError(
                "dbt-feature-flags injected in environment, this patch requires the env var DBT_FF_API_KEY"
            )

        self._key = "dbt-" + os.getenv("DBT_TARGET", "default")

        if sdk_key not in _factory_cache:
            factory = get_factory(sdk_key, config={"impressionsMode": "DEBUG"})
            factory.block_until_ready(5)
            _factory_cache[sdk_key] = factory

        self._client = _factory_cache[sdk_key].client()
        super().__init__()

    def _get_treatment(self, flag: str, default: t.Any) -> t.Any:
        """Evaluate a flag, mapping Split's 'control' sentinel to the provided default."""
        treatment = self._client.get_treatment(self._key, flag)
        return default if treatment == "control" else treatment

    def bool_variation(self, flag: str, default: bool = False) -> bool:
        treatment = self._get_treatment(flag, str(default))
        return str(treatment).lower() in ("on", "true")

    def string_variation(self, flag: str, default: str = "") -> str:
        return self._get_treatment(flag, default)

    def number_variation(self, flag: str, default: float | int = 0) -> float | int:
        treatment = self._get_treatment(flag, None)
        if treatment is None:
            return default
        try:
            return float(treatment)
        except (ValueError, TypeError):
            return default

    def json_variation(self, flag: str, default: JSONValue | None = None) -> JSONValue:
        result = self._client.get_treatment_with_config(self._key, flag)
        if result.treatment == "control" or result.config is None:
            return {} if default is None else default
        try:
            return json.loads(result.config)
        except (json.JSONDecodeError, TypeError):
            return {} if default is None else default
