from dataclasses import replace

from src.flood import (
    FloodDispatchDecisionEngine,
    SyntheticFloodWorldBuilder,
)


DECIDED_AT = "2026-07-25T08:30:00Z"


def evaluate_baseline():
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    return FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )


def test_baseline_flood_dispatch_is_cleared() -> None:
    result = evaluate_baseline()

    assert result.decision == "CLEARED_FOR_DISPATCH"
    assert result.cleared
    assert result.valid_until == "2026-07-25T09:00:00Z"
    assert result.failed_conditions == ()
    assert result.unknown_conditions == ()
    assert len(result.conditions) == 5


def test_flood_dispatch_is_deterministic() -> None:
    assert evaluate_baseline() == evaluate_baseline()


def test_expired_authority_blocks_dispatch() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        authority_valid_until="2026-07-25T08:00:00Z",
    )

    result = FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )

    assert result.decision == "BLOCKED"
    assert result.valid_until is None
    assert "DECISION_WITHIN_AUTHORITY" in result.failed_conditions


def test_superseded_plan_produces_superseded_decision() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        plan_status="SUPERSEDED",
        superseded_by="FRP-000002",
    )

    result = FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )

    assert result.decision == "SUPERSEDED"
    assert result.valid_until is None
    assert "PLAN_NOT_SUPERSEDED" in result.failed_conditions


def test_missing_authority_is_insufficient_evidence() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        authority_valid_until=None,
    )

    result = FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )

    assert result.decision == "INSUFFICIENT_EVIDENCE"
    assert result.valid_until is None
    assert (
        "DECISION_WITHIN_AUTHORITY"
        in result.unknown_conditions
    )


def test_closed_route_blocks_dispatch_through_eligibility() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    route = world.get_object("RTE-000001")

    world.registry._objects["RTE-000001"] = replace(
        route,
        viability_status="CLOSED",
    )

    result = FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )

    assert result.decision == "BLOCKED"
    assert result.eligibility.outcome == "INELIGIBLE"
    assert "ELIGIBILITY_ESTABLISHED" in result.failed_conditions


def test_dispatch_preserves_eligibility_evidence() -> None:
    result = evaluate_baseline()

    assert set(result.eligibility.evidence_ids).issubset(
        set(result.evidence_ids)
    )