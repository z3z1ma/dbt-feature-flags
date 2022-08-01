from dbt_feature_flags.base import BaseFeatureFlagsClient


class HarnessFeatureFlagsClient(BaseFeatureFlagsClient):
    def __init__(self):
        # Lazy imports
        import logging
        import os
        import time

        from featureflags.client import CfClient, Target
        from featureflags.client import log as logger

        # Override default logging to preserve stderr (needed for dbt-bigquery)
        logger.setLevel(logging.CRITICAL)

        # Set up target
        self.target = Target(
            identifier="dbt-" + os.getenv("DBT_TARGET", "default"),
            name=os.getenv("DBT_TARGET", "default").title(),
        )

        # Get key
        FF_KEY = os.getenv("DBT_FF_API_KEY")
        if FF_KEY is None:
            raise RuntimeError(
                "dbt-feature-flags injected in environment, this patch requires the env var DBT_FF_API_KEY"
            )

        # Init client
        self.client = CfClient(FF_KEY)
        time.sleep(float(os.getenv("DBT_FF_DELAY", 1.0)))

    def bool_variation(self, flag: str) -> bool:
        return self.client.bool_variation(flag, target=self.target, default=False)

    def string_variation(self, flag: str) -> str:
        return self.client.string_variation(flag, target=self.target, default="")

    def number_variation(self, flag: str) -> float | int:
        return self.client.number_variation(flag, target=self.target, default=0)

    def json_variation(self, flag: str) -> dict | list:
        return self.client.json_variation(flag, target=self.target, default={})
