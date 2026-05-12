"""Engine version + exports smoke tests for M1.11a."""

from __future__ import annotations

import engine
from engine.collar_builder import (
    CollarIntent,
    CollarLeg,
    CollarStructure,
    build,
)


def test_engine_version_bumped_to_1_5_0() -> None:
    """M1.11a is the version 1.5.0 bump per dev spec."""
    assert engine.__version__ == "1.5.0"


def test_collar_builder_exports_via_engine_namespace() -> None:
    """`from engine import CollarIntent, CollarLeg, CollarStructure, build_collar`
    must succeed — these are the public surface promised by the dev spec."""
    assert engine.CollarIntent is CollarIntent
    assert engine.CollarLeg is CollarLeg
    assert engine.CollarStructure is CollarStructure
    assert engine.build_collar is build


def test_collar_builder_in_engine_all() -> None:
    """The four collar_builder symbols are in `engine.__all__`."""
    expected = {"CollarIntent", "CollarLeg", "CollarStructure", "build_collar"}
    assert expected.issubset(set(engine.__all__))


def test_collar_intent_values_match_master_plan() -> None:
    """The three intents per master plan §7 + §9.10."""
    assert CollarIntent.ZERO_COST.value == "zero_cost"
    assert CollarIntent.INCOME.value == "income"
    assert CollarIntent.DEFENSIVE.value == "defensive"
    assert len(list(CollarIntent)) == 3
