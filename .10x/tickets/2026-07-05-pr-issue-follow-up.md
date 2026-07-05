Status: active
Created: 2026-07-05
Updated: 2026-07-05

# Assimilate Open PR Ideas and Close Issue

## Scope

Review open PRs without merging them, reimplement valid ideas directly on `main`, run the repository quality gates, commit and push, then close superseded PRs and reply to/close the open command-line usage issue.

## Acceptance Criteria

- PR #6 is inspected and any valid shutdown behavior is implemented directly on `main`.
- PR #7 is inspected and either reimplemented or recorded as superseded by the current Python/dbt support floor and UV CI matrix.
- Issue #3 is answered in repository documentation and then replied to on GitHub.
- Relevant tests cover new behavior.
- Robust local checks pass before push.
- GitHub PRs #6 and #7 are closed without merging.
- GitHub issue #3 is closed after a reply.

## Explicit Exclusions

- Do not merge PR #6 or PR #7.
- Do not restore the old dbt 1.0-1.7 CI matrix.
- Do not add back Poetry or persistent quality-tool dependencies.
- Do not change external provider configuration or rotate secrets.

## References

- https://github.com/z3z1ma/dbt-feature-flags/pull/6
- https://github.com/z3z1ma/dbt-feature-flags/pull/7
- https://github.com/z3z1ma/dbt-feature-flags/issues/3
- `.10x/knowledge/optional-provider-sdk-dependencies.md`
- `.10x/evidence/2026-07-05-pr-issue-follow-up.md`
- `.10x/reviews/2026-07-05-pr-issue-follow-up-review.md`

## Evidence Expectations

- Record PR/issue inspection outcome.
- Record final local check commands.
- Record commit and push.
- Record GitHub closure actions.

## Blockers

None.

## Progress and Notes

- 2026-07-05: Inspected PR #6. The shutdown hook idea is valid; `BaseFeatureFlagsClient.shutdown()` already exists on `main`, but Harness still needs a real SDK `destroy()` hook and `patch_dbt_environment()` should register real provider shutdown at process exit.
- 2026-07-05: Inspected PR #7. The old `pytz` and `MACRO_DEBUGGING` changes were valid for the prior dbt 1.0-1.7 CI matrix, but that matrix is superseded by the current audited Python 3.10+ and dbt-core 1.10.20+ floor plus UV CI installation.
- 2026-07-05: Inspected issue #3. The README does not clearly explain command-line flag control through dbt `--vars`, provider env vars, and `DBT_FF_DISABLE`.
- 2026-07-05: Implemented Harness shutdown, provider `atexit` registration, lifecycle tests, and README command-line docs.
- 2026-07-05: Ran local verification and recorded results in `.10x/evidence/2026-07-05-pr-issue-follow-up.md`.
