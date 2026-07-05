Status: recorded
Created: 2026-07-05
Updated: 2026-07-05
Relates-To: .10x/tickets/2026-07-05-pr-issue-follow-up.md

# PR and Issue Follow-Up Evidence

## What Was Observed

Open PRs #6 and #7 and issue #3 were inspected. PR #6 contained valid provider shutdown behavior that was not fully present on `main`; the remaining valid behavior was reimplemented directly on `main`. PR #7's old CI fixes were valid for the superseded dbt 1.0-1.7 matrix but are not applicable after the repository's Python 3.10+ and dbt-core 1.10.20+ floor. Issue #3 identified a real README gap for command-line flag control.

## Procedure

- Fetched open PRs and open issues from `z3z1ma/dbt-feature-flags`.
- Inspected PR #6 diff and comments.
- Inspected PR #7 diff and comments.
- Inspected issue #3 body and confirmed it had no comments.
- Implemented Harness provider shutdown via `client.destroy()`.
- Registered real provider shutdown from `patch_dbt_environment()` with `atexit`.
- Added tests for Harness shutdown, provider shutdown registration, and mock-client non-registration.
- Updated README command-line documentation for `--vars`, live provider env vars, and `DBT_FF_DISABLE`.

## Verification

- `uv run --frozen --with ruff ruff format --check .`
  - Exit code: 0.
- `uv run --frozen --with ruff ruff check .`
  - Exit code: 0.
- `uv run --frozen pytest -q`
  - Exit code: 0.
  - Result: `25 passed`.
- `uv run --frozen --all-extras --with ty ty check`
  - Exit code: 0.
- `uv run --frozen --all-extras --with mypy mypy .`
  - Exit code: 0.
- `uv run --frozen --with pytest-randomly --with pytest-timeout --with pytest-xdist pytest -q -n auto --timeout=300`
  - Exit code: 0.
  - Result: `25 passed`.
- `uv build`
  - Exit code: 0.
- `uv run --frozen --with coverage coverage run --branch -m pytest -q`
  - Exit code: 0.
  - Result: `25 passed`.
- `uv run --frozen --with coverage coverage report --show-missing`
  - Exit code: 0.
  - Result: 65.69% line coverage and 58.00% branch coverage.
- `uv run --frozen --with deptry deptry .`
  - Exit code: 0.
- `uv run --frozen --with pydoclint pydoclint dbt_feature_flags tests`
  - Exit code: 0.
- `uv audit --frozen`
  - Exit code: 0.
  - Result: no known vulnerabilities and no adverse project statuses in 75 packages.
- `uv run --frozen --with radon radon cc dbt_feature_flags tests -s -a`
  - Exit code: 0.
  - Result: average A complexity; max production function remains `preflight.run` at B (8).
- `uv run --frozen --with complexipy complexipy .`
  - Exit code: 0.
  - Result: all functions within allowed complexity.
- `uv run --frozen --with vulture vulture dbt_feature_flags tests --min-confidence 80`
  - Exit code: 0.
- `uv run --frozen --with vulture vulture dbt_feature_flags --min-confidence 80`
  - Exit code: 0.
- `uv run --frozen --with semgrep semgrep scan --config p/default --error --json --output /tmp/dbt-ff-pr-follow-up-semgrep.json --exclude .10x/evidence/.storage --exclude dist .`
  - Exit code: 0.
  - Result: 0 findings.
- `osv-scanner scan source -r . --format json --output /tmp/dbt-ff-pr-follow-up-osv.json`
  - Exit code: 0.
  - Result: 0 vulnerabilities.
- `gitleaks git --no-banner --redact --report-format json --report-path /tmp/dbt-ff-pr-follow-up-gitleaks-git.json .`
  - Exit code: 0.
- `gitleaks dir --no-banner --redact --report-format json --report-path /tmp/dbt-ff-pr-follow-up-gitleaks-dir.json .`
  - Exit code: 0.
- `npx --yes jscpd@5 . --reporters json,console --output /tmp/dbt-ff-pr-follow-up-jscpd --ignore "**/.venv/**,**/.git/**,**/__pycache__/**,**/.mypy_cache/**,**/.ruff_cache/**,**/.pytest_cache/**,**/dist/**,**/.10x/**"`
  - Exit code: 0.
  - Result: 0 clones and 0.00% duplicated lines.
- `codeql database create /tmp/dbt-ff-pr-follow-up-codeql-db --language=python --source-root . --overwrite`
  - Exit code: 0.
- `codeql database analyze /tmp/dbt-ff-pr-follow-up-codeql-db python-security-and-quality.qls --format=sarif-latest --output=/tmp/dbt-ff-pr-follow-up-codeql.sarif`
  - Exit code: 0.
  - Result: 0 results.

## What This Supports

- PR #6's remaining valid lifecycle behavior is implemented directly on `main` with tests.
- PR #7's proposed exact changes are superseded by the current support floor and CI design.
- Issue #3 is answered in README before the GitHub issue is closed.
- The local implementation is ready to commit and push before remote closure actions.

## Limits

- Live provider shutdown was not tested against real Harness credentials. The local test verifies the adapter calls the SDK `destroy()` boundary.
- GitHub PR/issue closure actions are recorded separately after the implementation is pushed.
