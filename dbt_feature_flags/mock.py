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


class MockFeatureFlagClient(BaseFeatureFlagsClient):
    def bool_variation(self, flag: str, default: bool = False) -> bool:
        self.logger.info("Mocking boolean flag %s with default return value", flag)
        return default

    def string_variation(self, flag: str, default: str = "") -> str:
        self.logger.info("Mocking string flag %s with default return value", flag)
        return default

    def number_variation(
        self, flag: str, default: Union[float, int] = 0
    ) -> Union[float, int]:
        self.logger.info("Mocking number flag %s with default return value", flag)
        return default

    def json_variation(
        self, flag: str, default: Optional[Union[dict, list]] = None
    ) -> Union[dict, list]:
        self.logger.info("Mocking json flag %s with default return value", flag)
        return {} if default is None else default
