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

from typing import Optional, Union

from dbt_feature_flags.base import BaseFeatureFlagsClient


class LaunchDarklyFeatureFlagsClient(BaseFeatureFlagsClient):
    def __init__(self):
        # Lazy imports
        import atexit
        import os

        import ldclient
        from ldclient.config import Config

        # Set up target
        self.target = {
            "key": "dbt-" + os.getenv("DBT_TARGET", "default"),
            "name": os.getenv("DBT_TARGET", "default").title(),
        }

        # Get key
        FF_KEY = os.getenv("DBT_FF_API_KEY")
        if FF_KEY is None:
            raise RuntimeError(
                "dbt-feature-flags injected in environment, this patch requires the env var DBT_FF_API_KEY"
            )

        # Init client
        ldclient.set_config(Config(FF_KEY))
        self.client = ldclient.get()
        if not self.client.is_initialized():
            raise RuntimeError(
                "LaunchDarkly SDK failed to initialize, ensure (DBT_FF_API_KEY=%s) is correct.",
                FF_KEY,
            )

        def exit_handler(c: ldclient.LDClient):
            c.close()

        atexit.register(exit_handler, self.client)
        super().__init__()

    def bool_variation(self, flag: str, default: bool = False) -> bool:
        return self.client.variation(flag, user=self.target, default=default)

    def string_variation(self, flag: str, default: str = "") -> str:
        return self.client.variation(flag, user=self.target, default=default)

    def number_variation(
        self, flag: str, default: Union[float, int] = 0
    ) -> Union[float, int]:
        return self.client.variation(flag, user=self.target, default=default)

    def json_variation(
        self, flag: str, default: Optional[Union[dict, list]] = None
    ) -> Union[dict, list]:
        return self.client.variation(
            flag, user=self.target, default={} if default is None else default
        )
