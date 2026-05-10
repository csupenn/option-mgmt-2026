# Changelog

All notable changes to the engine package (`packages/engine/engine/__version__`) and to top-level project shape are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); engine versioning follows [SemVer](https://semver.org/) per [ADR-0005](./docs/decisions/0005-engine-pure-function-discipline.md).

Version bump rules (per ADR-0005 + plan v1.2 §22.15 L2):

- **patch** (`0.x.y → 0.x.y+1`) — bug fix, no schema change
- **minor** (`0.x.0 → 0.x+1.0`) — new engine, score, or public function
- **major** (`x.0.0 → x+1.0.0`) — schema change, removed/renamed fields, semantic shift

CI guard `scripts/check_engine_version_bump.sh` enforces a version bump on every change under `packages/engine/engine/`.

---

## [0.5.0] — 2026-05-10

### Added (engine — `engine.scoring`)

- **`scoring.iv_score()`** — composite IV-favorability score in `[0, 1]` from `iv_rank`, `iv_percentile`, `hv_30`, `atm_iv_30d`. Higher = more favorable for selling premium.
  - rank component (weight 0.40), percentile component (weight 0.30), IV/HV premium component (weight 0.30; ratio anchors 0.7 → 0.0, 1.5 → 1.0).
  - Constant-prices fallback (`hv_30 == 0`) → premium component clamps to 0.5 (the "no information" prior).
- **`scoring.structure_score()`** — composite options-structure score in `[0, 1]` from `oi_walls`, `max_pain`, `spot`, `expected_move_pct`, `dte_to_nearest_opex`. Higher = more constrained structural environment.
  - wall proximity (weight 0.30) — distance to nearest OI wall normalized by 2·EM
  - pin alignment (weight 0.25) — distance from spot to max_pain normalized by EM
  - opex proximity (weight 0.20) — `[NEAR=2, FAR=14]` trading-day band
  - EM containment (weight 0.25) — `[TIGHT=2%, WIDE=10%]` band
  Handles one-sided walls (only support OR resistance present), zero-EM (zero-DTE) edge case correctly.
- **`scoring.event_score()`** — composite event-uncertainty score in `[0, 1]` from `days_to_event`, `event_kind`, `event_history`. Higher = larger event-driven risk premium in the chain.
  - Multiplicative proximity gate: `days_to_event is None` or `>= 30` collapses score to 0.
  - Inner blend: `0.5 · kind_weight + 0.5 · magnitude` where magnitude saturates at `avg_abs_return_pct ≥ 5%`.
  - Negative `days_to_event` (event already past) clamps to 0 (defensive — event-calendar service should advance promptly).
- **`scoring.OiWalls`** — frozen dataclass holding OI-derived support/resistance levels. Either side may be `None`; `structure_score` handles missing walls correctly. Produced by Flow Score Engine in M1.5; consumed by `structure_score` here.
- **`scoring.EventStats`** — frozen dataclass holding historical event-day stats (`avg_abs_return_pct`, `iv_runup_pct`, `sample_count`).
- **`scoring.EventKind`** — `StrEnum` of recognized event kinds (`earnings`, `fomc`, `cpi`, `guidance`, `ex_dividend`, `other`).
- **`scoring.EVENT_KIND_WEIGHTS`** — V1 weight prior table (`earnings=1.0`, `fomc=0.7`, `cpi=0.6`, `guidance=0.5`, `ex_dividend=0.3`, `other=0.5`). Replaced in Phase 4 by the M4.5 event-impact estimator (per plan §16).
- **Result types**: `IvScoreResult`, `StructureScoreResult`, `EventScoreResult`. Each carries `score: float ∈ [0, 1]` plus a `breakdown: dict[str, float]` mapping component names to their values (consumed by Confidence Composer for explainability per §22.13).

### Changed

- `engine.__init__` re-exports the new scoring symbols.
- 59 new tests (121 → 180 total in `packages/engine/tests/`). 100% line coverage on `engine.scoring` (per plan v1.2 §9.11 acceptance bar).

### CI

- New step `Coverage check (engine.scoring 100%)` enforces the 100% line-coverage requirement from plan v1.2 §9.11 via `pytest --cov=engine.scoring --cov-fail-under=100`.
- `pytest-cov` added to `packages/engine/pyproject.toml` dev dependencies.

### Plan refs

v1.2 §9.11 (Scoring Functions Module spec), §17 M1.4a (size M), §22.5 (`clip01` reuse), §22.13 (breakdown for Confidence Composer).

PR: [#TBD](https://github.com/csupenn/option-mgmt-2026/pulls)

---

## [0.4.0] — 2026-05-10

### Added (engine — `engine.market_state`)

- **`trend_strength.compute_trend_strength()`** — J. Welles Wilder Jr.'s ADX (1978), normalized to `[0, 1]`. ADX ≤ 20 → 0.0; ADX ≥ 40 → 1.0; linear between. Returns `0.5` sentinel when history < `2n + 10` bars (deliberate non-raising path per plan §22.5 so M1.4 `classify()` keeps running against partial data).
- **`trend_strength.wilder_adx()`** — exposed publicly as a diagnostic helper. Raises below the mathematical minimum of `2n + 1` bars.
- **`breakout.compute_breakout_signal()`** — 4-component composite, `[0, 1]`:
  - move (weight 0.35) — `|Δspot / spot_5d_ago| / 0.05`
  - vol (weight 0.20) — `atm_iv_change_5d / 0.10` (negatives clipped to 0)
  - oi (weight 0.20) — `|oi_shift_ratio|`
  - break (weight 0.25) — `above_resistance_pct / 0.02`, gated on `above_resistance` flag
  Weights sum to 1.0. Raises on non-positive `spot` or `spot_5d_ago`.
- **`engine._utils.clip01()`** — engine-wide `[0, 1]` saturation helper, centralized for reuse by M1.4 scoring functions and the Confidence Composer (per plan v1.2 §22.5 + §22.13).

### Changed

- 31 new tests added (90 → 121 total in `packages/engine/tests/`).

### Plan refs

v1.2 §9.1, §17 M1.3 (size S), §22.3 (extended `classify()` signature names `trend_strength` + `breakout_signal`), §22.5 (canonical formulas).

PR: [#26](https://github.com/csupenn/option-mgmt-2026/pull/26)

---

## [0.3.0] — 2026-05-10

### Added (engine — `engine.market_state`)

- **`max_pain.compute_max_pain()`** — CBOE-style total-OI loss minimization across the strike grid.
- **`expected_move.compute_expected_move()`** — ATM straddle method + forward-IV method, with cross-validation between the two.
- **`pcr.compute_pcr()`** — put/call ratios on volume and open interest (separate fields).

### Plan refs

v1.2 §9.1, §17 M1.2, §22.3.

PR: [#25](https://github.com/csupenn/option-mgmt-2026/pull/25)

---

## [0.2.0] — 2026-05-10

### Added (engine — `engine.market_state`)

- **`iv.compute_iv_rank()`** + **`iv.compute_iv_percentile()`** — 252-day rank and percentile from `iv_history` series.
- **`hv.compute_hv_30()`** — annualized close-to-close standard deviation.
- **`hv.compute_hv_30_parkinson()`** — Parkinson high-low range estimator (~5× more efficient than close-to-close).

### Added (seeds)

- 252-day MSFT IV history seed CSV per plan v1.2 §21.

### Plan refs

v1.2 §9.1, §17 M1.1, §22.5 (IV rank formula).

PR: [#24](https://github.com/csupenn/option-mgmt-2026/pull/24)

---

## [0.1.0] — 2026-05-10

Initial engine scaffold (M0.6).

### Added

- `engine.regimes` — 6 named regimes per [ADR-0002](./docs/decisions/0002-regime-taxonomy.md): `HIGH_IV_EVENT`, `HIGH_IV_PIN`, `LOW_IV_TREND`, `LOW_IV_RANGE`, `BREAKOUT`, `POST_EVENT_REPRICE`.
- `engine.profiles.UserStrategyProfile` — frozen Pydantic v2 model (style, max_coverage, roll_aggressiveness, drawdown_tolerance, tax_sensitivity, delta/DTE bands).
- `engine.types` — `OptionContract`, `ChainSnapshot`, `ChainRow`.
- `engine.version` — `__version__` constant; bumped per ADR-0005 / plan §22.15 L2.
- `packages/shared-types/` — TS types generated from Pydantic via `scripts/generate.py`. CI drift check.

### Plan refs

v1.2 §17 M0.6, §22.2 (FlowScore V1 contract names), §22.3 (`classify()` signature shape).

PR: [#17](https://github.com/csupenn/option-mgmt-2026/pull/17)

---

## Pre-engine — Phase 0 foundation (no engine version)

Phase 0 milestones M0.1–M0.5 + M0.7 + the docs foundation (ADRs 0001–0007) shipped before the engine package was scaffolded; they're tracked in [`README.md` § Status](./README.md#status), not here. The engine version line begins at `0.1.0` (M0.6).

| Date | What | PR |
|---|---|---|
| 2026-05-10 | docs — enhancement-spec adoption roadmap (ADR-0008) | [#23](https://github.com/csupenn/option-mgmt-2026/pull/23) |
| 2026-05-10 | M0.7 — end-to-end smoke test | [#22](https://github.com/csupenn/option-mgmt-2026/pull/22) |
| 2026-05-10 | M0.5 — CI + pre-commit + Dependabot + policy guards | [#6](https://github.com/csupenn/option-mgmt-2026/pull/6) |
| 2026-05-10 | docs foundation + ADRs 0001–0006 | [#5](https://github.com/csupenn/option-mgmt-2026/pull/5) |
| 2026-05-10 | M0.4 — Next.js shell + disclaimer gate + Tailwind + Vitest | [#4](https://github.com/csupenn/option-mgmt-2026/pull/4) |
| 2026-05-10 | M0.3 — FastAPI shell + auth scaffolding | [#3](https://github.com/csupenn/option-mgmt-2026/pull/3) |
| 2026-05-10 | M0.2 — Postgres schema + Alembic init | [#2](https://github.com/csupenn/option-mgmt-2026/pull/2) |
| 2026-05-10 | M0.1 — monorepo scaffold | [#1](https://github.com/csupenn/option-mgmt-2026/pull/1) |
