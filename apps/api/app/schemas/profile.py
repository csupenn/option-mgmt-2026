"""Request/response shapes for `GET/PUT /profile` (M1.17).

Per plan v1.2 §7 + §9.9 + §17 M1.17.

The profile is the user's `UserStrategyProfile` (per engine.profiles).
It is persisted to `users.strategy_profile` JSONB (column already exists
from M0.2 / §22.6) and hydrated into the engine on every `/daily-plan`
call.

Validation rules per §9.9 — all enforced by `UserStrategyProfile`'s
Pydantic constraints; we don't re-implement them here. The Pydantic
validation surface at the API boundary catches:

  - max_position_pct ∈ [0, 1]
  - max_coverage_pct ∈ [0, 1]
  - min_iv_rank_for_short_premium ∈ [0, 100]
  - drawdown_tolerance ∈ [0, 1]
  - risk_tolerance ∈ enum {conservative, moderate, aggressive}
  - income_need ∈ enum {low, medium, high}
  - style ∈ enum {income, balanced, growth}

`PUT /profile` accepts a `UserStrategyProfile` directly — the request
body is the new profile in full (PUT semantics, not PATCH). For partial
updates use repeated GET → mutate → PUT round-trips.

This file is intentionally thin: the engine package owns the schema
shape (the `UserStrategyProfile` BaseModel), and we re-export + use
Pydantic's `extra="forbid"` to reject unknown fields at the API layer.
"""

from __future__ import annotations

from engine.profiles import UserStrategyProfile

# `UserStrategyProfile` from the engine is the source of truth for the
# profile shape AND validation rules. We re-export it here so callers can
# `from app.schemas.profile import UserStrategyProfile` rather than reach
# directly into the engine package.

ProfileResponse = UserStrategyProfile
ProfileUpdateRequest = UserStrategyProfile


__all__ = [
    "ProfileResponse",
    "ProfileUpdateRequest",
    "UserStrategyProfile",
]
