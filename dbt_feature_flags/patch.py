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

import os
from enum import Enum

from dbt_feature_flags import base, harness, launchdarkly, mock


class SupportedProviders(str, Enum):
    Harness = "harness"
    LaunchDarkly = "launchdarkly"
    NoopClient = "mock"


def _get_client() -> base.BaseFeatureFlagsClient:
    """Return the user specified client, valid impementations MUST
    inherit from BaseFeatureFlagsClient"""
    ff_provider = os.getenv("FF_PROVIDER")
    ff_client = None
    if os.getenv("DBT_FF_DISABLE") or not ff_provider:
        ff_client = mock.MockFeatureFlagClient()
    elif ff_provider == SupportedProviders.Harness:
        ff_client = harness.HarnessFeatureFlagsClient()
    elif ff_provider == SupportedProviders.LaunchDarkly:
        ff_client = launchdarkly.LaunchDarklyFeatureFlagsClient()
    if not isinstance(ff_client, base.BaseFeatureFlagsClient):
        raise RuntimeError(
            "Invalid feature flag client specified by (FF_PROVIDER=%s)",
            ff_provider,
        )
    return ff_client


def patch_dbt_environment() -> None:
    import functools

    from dbt.clients import jinja

    # Getting environment function from dbt
    jinja._get_environment = jinja.get_environment

    # FF client
    ff_client = _get_client()

    def add_ff_extension(func):
        if getattr(func, "status", None) == "patched":
            return func

        @functools.wraps(func)
        def with_ff_extension(*args, **kwargs):
            env = func(*args, **kwargs)
            env.globals["feature_flag"] = ff_client.bool_variation
            env.globals["feature_flag_str"] = ff_client.string_variation
            env.globals["feature_flag_num"] = ff_client.number_variation
            env.globals["feature_flag_json"] = ff_client.json_variation
            return env

        with_ff_extension.status = "patched"

        return with_ff_extension

    env_with_ff = add_ff_extension(jinja._get_environment)

    jinja.get_environment = env_with_ff


if __name__ == "__main__":
    patch_dbt_environment()
