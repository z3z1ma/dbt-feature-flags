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

"""Preflight check for dbt feature flag cache invalidation.

Compares current flag states against the states from the previous dbt run.
If any config-layer flags have changed, deletes target/partial_parse.msgpack
to force dbt to re-parse all models — ensuring config(enabled=feature_flag(...))
blocks are re-evaluated with the latest flag values.

If nothing has changed, partial parsing proceeds normally with no performance cost.

Usage (CLI):
    dbt-ff-preflight --flags enable_new_mart enable_experimental_model
    dbt run --profiles-dir .

Usage (Python):
    from dbt_feature_flags.preflight import run
    run(flags=["enable_new_mart"], target_dir="target")
"""

from __future__ import annotations

import argparse
import json
import pathlib
import typing as t

from dbt_feature_flags.base import BaseFeatureFlagsClient


def run(flags: list[str], target_dir: str = "target") -> None:
    """Check if any config-layer feature flags have changed since the last run.

    If a change is detected, deletes partial_parse.msgpack so dbt performs
    a full re-parse on the next run. Persists the current flag states to
    a cache file for comparison on the next invocation.

    :param flags: List of flag names that are used in model config() blocks
                  or dbt_project.yml +enabled directives.
    :param target_dir: Path to the dbt target directory (default: "target").
    """
    from dbt_feature_flags.patch import _get_client, _MOCK_CLIENT

    target = pathlib.Path(target_dir)
    cache_file = target / ".fme_flag_state.json"
    partial_parse = target / "partial_parse.msgpack"

    client = _get_client()

    if client is _MOCK_CLIENT:
        print("[dbt-ff] Running in mock mode — skipping preflight flag check.")
        return

    feature_client = t.cast(BaseFeatureFlagsClient, client)
    current = {flag: feature_client.bool_variation(flag, False) for flag in flags}
    feature_client.shutdown()

    # Compare to previous run
    previous = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    changed = {
        f: (previous.get(f, None), v)
        for f, v in current.items()
        if v != previous.get(f)
    }

    if changed:
        print("[dbt-ff] Flag state changed — forcing full re-parse")
        for flag, (before, after) in changed.items():
            print(f"[dbt-ff]   {flag}: {before} -> {after}")
        partial_parse.unlink(missing_ok=True)
    else:
        print("[dbt-ff] Flag state unchanged — partial parse OK")

    # Persist current state for next run
    target.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(current, indent=2))


def cli() -> None:
    """Entry point for the dbt-ff-preflight CLI command."""
    parser = argparse.ArgumentParser(
        description=(
            "Check if config-layer feature flags have changed and invalidate "
            "dbt's partial parse cache if so."
        )
    )
    parser.add_argument(
        "--flags",
        nargs="+",
        required=True,
        metavar="FLAG",
        help="Flag names used in model config() blocks or dbt_project.yml +enabled.",
    )
    parser.add_argument(
        "--target-dir",
        default="target",
        metavar="DIR",
        help="Path to the dbt target directory (default: target).",
    )
    args = parser.parse_args()
    run(flags=args.flags, target_dir=args.target_dir)


if __name__ == "__main__":
    cli()
