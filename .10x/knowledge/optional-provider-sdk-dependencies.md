Status: active
Created: 2026-07-05
Updated: 2026-07-05

# Optional Provider SDK Dependencies

`dbt-feature-flags` exposes provider integrations as optional extras:

- `harness`: `harness-featureflags`
- `fme`: `splitio-client`
- `launchdarkly`: `launchdarkly-server-sdk`

Provider modules should keep SDK imports lazy so the base package can be imported, tested, type-checked, and scanned without installing every provider extra. Use `importlib.import_module()` inside provider constructors for optional SDK modules, and keep the public package dependency metadata in `[project.optional-dependencies]`.

Deptry does not currently infer that these optional extras are used through lazy provider imports, so `pyproject.toml` carries a narrow `DEP002` ignore for only these three optional SDK packages. Do not broaden that ignore to required dependencies or unrelated extras.

The current audited support floor is Python 3.10+ and `dbt-core>=1.10.20,<2`. That floor is tied to `uv audit` and OSV cleanliness for the generated `uv.lock`.
