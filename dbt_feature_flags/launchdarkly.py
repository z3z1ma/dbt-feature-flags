from typing import Union

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

    def bool_variation(self, flag: str) -> bool:
        v = self.client.variation(flag, user=self.target, default=False)
        if not isinstance(v, bool):
            raise ValueError(
                "Non boolean return type found for feature_flag call, use appropriate feature_flag_* call"
            )
        return v

    def string_variation(self, flag: str) -> str:
        v = self.client.variation(flag, user=self.target, default="")
        if not isinstance(v, str):
            raise ValueError(
                "Non string return type found for feature_flag_str call, use appropriate feature_flag_* call"
            )
        return v

    def number_variation(self, flag: str) -> Union[float, int]:
        v = self.client.variation(flag, user=self.target, default=0)
        if not isinstance(v, (float, int)):
            raise ValueError(
                "Non number return type found for feature_flag_num call, use appropriate feature_flag_* call"
            )
        return v

    def json_variation(self, flag: str) -> Union[dict, list]:
        v = self.client.variation(flag, user=self.target, default={})
        if not isinstance(v, (dict, list)):
            raise ValueError(
                "Non JSON return type found for feature_flag_json call, use appropriate feature_flag_* call"
            )
        return v
