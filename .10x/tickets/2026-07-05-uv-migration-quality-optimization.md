Status: active
Created: 2026-07-05
Updated: 2026-07-05

# UV Migration and Quality Optimization

## Scope

Migrate the repository from Poetry metadata and lock management to PEP 621 project metadata with a `uv.lock`, then run the production Python quality optimizer procedure from the attached agent specification against the repository.

## Acceptance Criteria

- `pyproject.toml` uses standard `[project]` metadata instead of `[tool.poetry]`.
- `poetry.lock` is removed.
- `uv.lock` is generated.
- The package entry point, version, optional provider extras, README metadata, repository URL, homepage URL, and Python compatibility floor are preserved unless tool evidence proves a required change.
- The quality toolchain from the supplied procedure is run where available and relevant.
- Hard gates either pass or have explicit recorded blockers/limits.
- Metric outputs are compared before and after meaningful quality edits.
- Obvious repository issues discovered during the pass are fixed when they are in scope and verifiable.
- Commits are created at coherent milestones.

## Explicit Exclusions

- Do not rotate secrets or alter external service state.
- Do not initialize new architecture, Semgrep, coverage, or benchmark baselines.
- Do not add persistent quality-tool dependencies unless needed for project behavior or explicitly justified by the migration.
- Do not broaden product behavior beyond documented dbt feature flag behavior.

## References

- `/Users/alexanderbut/.codex/attachments/e69acfe5-be34-40e3-bb7f-c43ea0e42e64/pasted-text.txt`
- `pyproject.toml`
- `README.md`
- `tests/test_dbt_feature_flags.py`

## Evidence Expectations

- Record packaging migration checks.
- Record test/type/lint/security/dependency/complexity command results.
- Record any skipped external tools and the reason.
- Record closure review before moving the ticket to done.

## Blockers

None.

## Progress and Notes

- 2026-07-05: Started from a clean `main` worktree and created branch `codex/uv-quality-optimizer`.
- 2026-07-05: Converted Poetry metadata to PEP 621 metadata, removed `poetry.lock`, generated `uv.lock`, built distributions with `uv build`, and passed `uv run --frozen pytest -q`.
