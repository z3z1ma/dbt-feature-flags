"""See README for usage details 
or on how to implement a new client
"""
import os

from dbt_feature_flags import base, mock, harness, launchdarkly


def _get_client() -> base.BaseFeatureFlagsClient:
    """Return the user specified client, valid impementations MUST
    inherit from BaseFeatureFlagsClient"""
    if os.getenv("DBT_FF_DISABLE"):
        return mock.MockFeatureFlagClient()
    ff_provider = os.getenv("FF_PROVIDER", "harness")
    ff_client = None
    if ff_provider == "harness":
        ff_client = harness.HarnessFeatureFlagsClient()
    elif ff_provider == "launchdarkly":
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

    if os.getenv("DBT_FF_TEST"):
        test_ff_eval()


def test_ff_eval() -> None:
    from dbt.clients.jinja import get_environment

    template = get_environment().from_string(
        """
    {%- if feature_flag("Test_Flag") %}
    select 100 as _ff_true
    {%- else %}
    select -100 as _ff_false
    {% endif -%}
    """
    )
    print(template.render())
