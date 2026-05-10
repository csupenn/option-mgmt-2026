# ADR-0007: Python 3.13 pinned across api + engine

**Status**: Accepted
**Date**: 2026-05-10
**Plan ref**: v1.2 §17 M0.5 (CI), §22.15 (pin discipline)
**Related code**:

- `pyproject.toml` (root) — `requires-python = ">=3.13"`, `target-version = "py313"`, `python_version = "3.13"`
- `apps/api/pyproject.toml` — same set
- `apps/api/.python-version` — `3.13` (uv reads this)
- `apps/api/Dockerfile` — `FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim`, runtime `python:3.13-slim`
- `.github/workflows/ci.yml` — `astral-sh/setup-uv@v3` with `python-version: '3.13'`
- `packages/engine/pyproject.toml` — same set when M0.6 ships

## Context

The project initially pinned Python 3.12 (released 2023-10, mature). As of 2026-05-10:

- Python 3.13 was released 2024-10. **18 months of production hardening.** All our deps (fastapi, sqlalchemy, alembic, psycopg, pydantic, argon2-cffi, jose, ruff, mypy, pytest, hypothesis, py_vollib) ship 3.13 wheels.
- Python 3.14 was released 2026-04-14. **One month old.** Latest, but scientific stack (numpy, scipy, py_vollib) wheel availability is uneven this early. Risky for an MVP that needs reliable installs.

Choosing the right pin balances staying current vs avoiding wheel-availability roulette.

## Decision

**Pin Python to 3.13** across the entire codebase.

Specifically:

- `requires-python = ">=3.13"` in every `pyproject.toml` (root, apps/api, packages/engine when shipped)
- `python-version: '3.13'` for `astral-sh/setup-uv` in CI
- `apps/api/.python-version` file (`3.13`) so `uv sync` selects the right interpreter without per-call flags
- `python:3.13-slim` (runtime) and `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (builder) in `apps/api/Dockerfile`
- `target-version = "py313"` for ruff (so it lints against 3.13 syntax)
- `python_version = "3.13"` for mypy (so it type-checks against 3.13 stdlib)

When 3.14 reaches ~12 months of broad ecosystem support (estimated 2027), open a follow-up ADR to bump.

## Consequences

**Positive**

- Access to 3.13 features: better error messages, tail-call interpreter, free-threading mode (PEP 703, experimental), incremental GC, `typing.TypeIs`.
- All deps support it; no wheel-availability drama.
- `tomllib` is in stdlib (relevant for any tooling that needs to read pyproject.toml).
- Mypy + ruff + pytest all have explicit 3.13 support.

**Negative**

- Slightly larger Docker images than 3.12 (~5-10 MB).
- One Python minor version away from latest (3.14). Anyone wanting bleeding-edge features will have to wait for the next bump.

**Neutral**

- `requires-python = ">=3.13"` rejects 3.12. Old developer setups need updating.

## Alternatives considered

1. **Stay on Python 3.12** (released 2023-10) — rejected: 19 months old; missing tail-call interpreter and improved error messages from 3.13 that genuinely help debugging.
2. **Bump to Python 3.14** (released 2026-04-14, latest stable) — rejected: too new for production. Scientific Python stack (numpy, scipy, py_vollib) wheel availability is uneven on Python releases this fresh. Wait until ~2027 for ecosystem maturity.
3. **Leave the pin loose** (`requires-python = ">=3.12"`) — rejected: violates the "single canonical pin" principle from `docs/engineering-principles.md` (Pin discipline). CI builds become non-deterministic across runner versions.

## Enforcement

- CI explicitly sets `python-version: '3.13'` on `astral-sh/setup-uv@v3` so runner-default Python doesn't sneak in.
- `apps/api/.python-version` makes local `uv` invocations consistent with CI without per-call `--python` flags.
- A future stretch goal: `scripts/check_python_version.sh` similar to `check_next_version.sh` (M0.7+ if needed).

## References

- Plan v1.2 §22.15 — pin discipline
- Plan v1.2 §17 M0.5 — CI pipelines
- [ADR-0005](./0005-engine-pure-function-discipline.md) — engine pure-function discipline (engine deps need to install on 3.13)
- Python 3.13 release notes: https://docs.python.org/3.13/whatsnew/3.13.html
- Python 3.14 release notes: https://docs.python.org/3.14/whatsnew/3.14.html
