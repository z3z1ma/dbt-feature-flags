from dbt_feature_flags.patch import patch_dbt_environment

patch_dbt_environment()


def test_ff_eval_1() -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    assert (
        get_rendered(
            """
    {%- set test_case -%}
        {%- if feature_flag("Test_Flag", default=False) -%}
            select 100 as invalid
        {%- else -%}
            select -100 as valid
        {%- endif -%}
    {%- endset -%}
    {{- test_case | trim -}}
    """,
            generate_base_context({}),  # type: ignore
        )
        == "select -100 as valid"
    )


def test_ff_eval_2() -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    assert (
        get_rendered(
            """
    {%- set test_case -%}
        {%- if feature_flag("Test_Flag", default=True) -%}
            select 100 as valid
        {%- else -%}
            select -100 as invalid
        {%- endif -%}
    {%- endset -%}
    {{- test_case | trim -}}
    """,
            generate_base_context({}),  # type: ignore
        )
        == "select 100 as valid"
    )


def test_ff_eval_nested() -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    assert (
        get_rendered(
            """
    {%- set test_case -%}
        {%- if feature_flag("Test_Flag", default=feature_flag("Nested_Flag", default=True)) -%}
            select 100 as valid
        {%- else -%}
            select -100 as invalid
        {%- endif -%}
    {%- endset -%}
    {{- test_case | trim -}}
    """,
            generate_base_context({}),  # type: ignore
        )
        == "select 100 as valid"
    )


def test_ff_eval_with_var() -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    assert (
        get_rendered(
            """
    {%- set test_case -%}
        {%- if feature_flag("Test_Flag", default=var("Dbt_Var", default=True)) -%}
            select 100 as valid
        {%- else -%}
            select -100 as invalid
        {%- endif -%}
    {%- endset -%}
    {{- test_case | trim -}}
    """,
            generate_base_context({}),
        )
        == "select 100 as valid"
    )


def test_ff_eval_with_var_overriden_by_cli() -> None:
    from dbt.clients.jinja import get_rendered
    from dbt.context.base import generate_base_context

    assert (
        get_rendered(
            """
    {%- set test_case -%}
        {%- if feature_flag("Test_Flag", default=var("Dbt_Var", default=True)) -%}
            select 100 as invalid
        {%- else -%}
            select -100 as valid
        {%- endif -%}
    {%- endset -%}
    {{- test_case | trim -}}
    """,
            generate_base_context({"Dbt_Var": False}),
        )
        == "select -100 as valid"
    )
