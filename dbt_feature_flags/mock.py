from typing import Union

from dbt_feature_flags.base import BaseFeatureFlagsClient


class MockFeatureFlagClient(BaseFeatureFlagsClient):
    def bool_variation(self, flag: str) -> bool:
        return False

    def string_variation(self, flag: str) -> str:
        return ""

    def number_variation(self, flag: str) -> Union[float, int]:
        return 0

    def json_variation(self, flag: str) -> Union[dict, list]:
        return {}
