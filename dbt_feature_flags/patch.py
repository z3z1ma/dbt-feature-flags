"""
Set up feature flags:
    https://harness.io/products/feature-flags

Configurable env vars:
    DBT_FF_API_KEY (required)
        the API key for the Harness Feature Flags instance
    DBT_FF_DISABLE 
        disables patch if detected in env regardless of set value
    DBT_FF_DELAY
        length of time to delay after client instantiation for initial load
"""

def patch_dbt_environment() -> None:
    import os

    if os.getenv("DBT_FF_DISABLE"):
        return
    
    FF_KEY = os.getenv("DBT_FF_API_KEY")
    if FF_KEY is None:
        raise RuntimeError("dbt-feature-flags injected in environment, this patch requires the env var DBT_FF_API_KEY")

    import functools
    import logging
    import time

    from dbt.clients import jinja
    from featureflags.client import CfClient, Target, log

    # Override default logging to preserve stderr
    log.setLevel(logging.CRITICAL)

    # Getting environment function from dbt
    jinja._get_environment = jinja.get_environment

    # FF client
    ff_client = CfClient(FF_KEY)
    time.sleep(float(os.getenv("DBT_FF_DELAY", 1.0)))

    def add_ff_extension(func):
        if getattr(func, "status", None) == "patched":
            return func
        
        @functools.wraps(func)
        def with_ff_extension(*args, **kwargs):
            env = func(*args, **kwargs)
            target = Target(
                identifier="dbt-feature-flags", name=os.getenv("DBT_TARGET", "default")
            )
            bool_variation = functools.partial(ff_client.bool_variation, target=target, default=False)
            string_variation = functools.partial(ff_client.string_variation, target=target, default="")
            number_variation = functools.partial(ff_client.number_variation, target=target, default=0)
            json_variation = functools.partial(ff_client.json_variation, target=target, default={})
            env.globals["feature_flag"] = bool_variation
            env.globals["feature_flag_str"] = string_variation
            env.globals["feature_flag_num"] = number_variation
            env.globals["feature_flag_json"] = json_variation
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
