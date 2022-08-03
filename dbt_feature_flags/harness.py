from typing import Optional, Union

from dbt_feature_flags.base import BaseFeatureFlagsClient


class HarnessFeatureFlagsClient(BaseFeatureFlagsClient):
    def __init__(self):
        # Lazy imports
        import logging
        import os

        from featureflags.api.client import Client
        from featureflags.api.default.get_all_segments import sync as retrieve_segments
        from featureflags.api.default.get_feature_config import sync as retrieve_flags
        from featureflags.client import CfClient, Target
        from featureflags.client import log as logger
        from featureflags.config import Config
        from featureflags.evaluations.evaluator import Evaluator
        from featureflags.repository import Repository

        # Override default logging to preserve stderr (needed for dbt-bigquery)
        logger.setLevel(logging.CRITICAL)

        class CfSyncClient(CfClient):
            def __init__(self, sdk_key: str):
                self._sdk_key: Optional[str] = sdk_key
                self._config: Config = Config(
                    enable_stream=False, enable_analytics=False
                )

                # Set by authenticate
                self._client: Optional[Client] = None
                self._auth_token: Optional[str] = None
                self._environment_id: Optional[str] = None
                self._cluster: str = "1"
                self.authenticate()

                self._repository = Repository(self._config.cache)
                self._evaluator = Evaluator(self._repository)
                flags = retrieve_flags(
                    client=self._client, environment_uuid=self._environment_id
                )
                for flag in flags:
                    self._repository.set_flag(flag)
                segments = retrieve_segments(
                    client=self._client, environment_uuid=self._environment_id
                )
                for segment in segments:
                    self._repository.set_segment(segment)

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
        self.client = CfSyncClient(FF_KEY)

    def bool_variation(self, flag: str) -> bool:
        return self.client.bool_variation(flag, target=self.target, default=False)

    def string_variation(self, flag: str) -> str:
        return self.client.string_variation(flag, target=self.target, default="")

    def number_variation(self, flag: str) -> Union[float, int]:
        return self.client.number_variation(flag, target=self.target, default=0)

    def json_variation(self, flag: str) -> Union[dict, list]:
        return self.client.json_variation(flag, target=self.target, default={})
