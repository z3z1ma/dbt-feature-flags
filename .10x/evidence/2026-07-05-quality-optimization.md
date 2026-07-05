Status: recorded
Created: 2026-07-05
Updated: 2026-07-05
Relates-To: .10x/tickets/done/2026-07-05-uv-migration-quality-optimization.md

# Quality Optimization Evidence

## What Was Observed

The production Python quality optimizer procedure was run against the repository after the Poetry-to-uv migration. Hard gates are passing, dependency/security findings were removed, coverage improved, and duplicate-code findings were eliminated.

Raw machine-readable reports are stored under `.10x/evidence/.storage/quality-2026-07-05/`.

## Procedure

- Repository discovery inspected Python metadata, source layout, tests, CI, and existing tool configuration.
- Baseline checks were captured before quality edits where the tool produced useful output.
- The implementation was edited to address tool findings and obvious in-scope defects:
  - removed stale Poetry workflow assumptions from CI and switched CI install/test commands to `uv`;
  - pinned GitHub Actions by SHA to resolve Semgrep supply-chain findings;
  - fixed unused code flagged by Ruff/CodeQL;
  - fixed the preflight runtime path by adding a base `shutdown()` no-op and testing cache invalidation behavior;
  - made optional provider SDK imports lazy through `import_module()` so type/dependency tooling can analyze the package without installed extras;
  - avoided mutable JSON defaults and tightened validator behavior;
  - expanded provider, patching, validator, and preflight tests.
- Final gates were run after edits and before commit.

## Metric Vector

| Metric | Baseline | Final |
| --- | ---: | ---: |
| Ruff format drift | 3 files | 0 files |
| Ruff lint errors | 2 | 0 |
| `ty` diagnostics | 23 | 0 |
| `mypy` errors | 14 | 0 |
| `pytest` | 5 passed | 23 passed |
| Coverage, imported modules | 48.91% line / 27.78% branch | 63.76% line / 56.25% branch |
| Coverage, package-wide source run | not used as baseline | 43.08% line / 56.25% branch |
| Radon max cyclomatic complexity | 8 | 9 overall, 8 production |
| Complexipy max cognitive complexity | 9 | 11 |
| Vulture findings | not blocking | 0 |
| Deptry findings | 3 optional-extra false positives before ignore | 0 |
| pydoclint violations | 0 | 0 |
| Semgrep findings | 2 | 0 |
| CodeQL findings | 2 | 0 |
| `uv audit` vulnerabilities | 35 | 0 |
| OSV packages with vulnerabilities | 12 | 0 |
| OSV vulnerabilities | 35 | 0 |
| Gitleaks findings | 0 | 0 |
| jscpd duplicate blocks | 3 | 0 |
| jscpd duplicated lines | 31 / 2.94% | 0 / 0.00% |

## Final Command Results

- `uv lock`
  - Exit code: 0.
- `uv build`
  - Exit code: 0.
  - Built `dist/dbt_feature_flags-0.5.2.tar.gz` and `dist/dbt_feature_flags-0.5.2-py3-none-any.whl`.
- `uv run --frozen --with ruff ruff format --check .`
  - Exit code: 0.
- `uv run --frozen --with ruff ruff check .`
  - Exit code: 0.
- `uv run --frozen --all-extras --with ty ty check`
  - Exit code: 0.
- `uv run --frozen --all-extras --with mypy mypy .`
  - Exit code: 0.
- `uv run --frozen pytest -q`
  - Exit code: 0.
  - Result: `23 passed`.
- `uv run --frozen --with pytest-randomly --with pytest-timeout --with pytest-xdist pytest -q -n auto --timeout=300`
  - Exit code: 0.
  - Result: `23 passed`.
- `uv run --frozen --with coverage coverage run --branch -m pytest -q`
  - Exit code: 0.
- `uv run --frozen --with coverage coverage json -o .10x/evidence/.storage/quality-2026-07-05/coverage-final.json`
  - Exit code: 0.
- `uv run --frozen --with radon radon cc dbt_feature_flags tests -s -a -j`
  - Exit code: 0.
- `uv run --frozen --with complexipy complexipy .`
  - Exit code: 0.
- `uv run --frozen --with vulture vulture dbt_feature_flags tests --min-confidence 80`
  - Exit code: 0.
- `uv run --frozen --with vulture vulture dbt_feature_flags --min-confidence 80`
  - Exit code: 0.
- `uv run --frozen --with deptry deptry .`
  - Exit code: 0.
- `uv run --frozen --with deptry deptry . --json-output .10x/evidence/.storage/quality-2026-07-05/deptry-final.json`
  - Exit code: 0.
  - Result: `[]`.
- `uv run --frozen --with pydoclint pydoclint dbt_feature_flags tests`
  - Exit code: 0.
- `uv run --frozen --with semgrep semgrep scan --config p/default --error --json --output .10x/evidence/.storage/quality-2026-07-05/semgrep-final.json --exclude .10x/evidence/.storage --exclude dist .`
  - Exit code: 0.
- `codeql database create ...` and `codeql database analyze ...`
  - Exit code: 0.
  - Result: 0 final SARIF results.
- `uv audit --frozen`
  - Exit code: 0.
- `osv-scanner scan source -r . --format json --output .10x/evidence/.storage/quality-2026-07-05/osv-final.json`
  - Exit code: 0.
- `gitleaks git --no-banner --redact --report-format json ... .`
  - Exit code: 0.
- `gitleaks dir --no-banner --redact --report-format json ... .`
  - Exit code: 0.
- `npx --yes jscpd@5 . --reporters json,console --output .10x/evidence/.storage/quality-2026-07-05/jscpd-final-clean --ignore "**/.venv/**,**/.git/**,**/__pycache__/**,**/.mypy_cache/**,**/.ruff_cache/**,**/.pytest_cache/**,**/dist/**,**/.10x/**"`
  - Exit code: 0.

## Skipped Tools and Limits

- Tach was skipped because the repository has no `tach.toml`; the procedure explicitly forbids initializing Tach without a policy decision.
- Hypothesis was not added because it is not an existing dependency and the validator/parser behavior was covered with direct regression tests rather than introducing a persistent property-testing dependency.
- pytest-benchmark was skipped because the repository has no benchmark tests and the work did not change a performance-sensitive path.
- Scalene and Memray were skipped because no performance or memory regression was under investigation.
- Coverage was recorded without xdist because the final xdist coverage invocation completed the tests but emitted no coverage data in this local environment. Randomized parallel pytest still ran separately and passed.
- Provider constructors are covered with fake SDK delegation tests, but real Harness, Harness FME, and LaunchDarkly credentialed integrations were not exercised.

## What This Supports

- The package now builds and tests from `uv.lock`.
- Hard quality gates in the supplied procedure either pass or have recorded, procedure-consistent skip reasons.
- Security and supply-chain findings observed at baseline were addressed.
- The dependency floor change removes vulnerable transitive dependency resolutions found in the baseline lock.

## Limits

- The Python/dbt support floor was intentionally raised to Python 3.10+ and dbt-core 1.10.20+ to maintain a clean audited lock. That is a compatibility change.
- Package-wide source coverage remains modest because optional provider initialization paths require real SDK setup and credentials; the behavior reachable without live providers is now covered.
