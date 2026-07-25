from dataclasses import replace

from src.flood import (
    FloodEligibilityEngine,
    SyntheticFloodWorldBuilder,
)


EVALUATED_AT = "2026-07-25T08:30:00Z"


def evaluate_baseline():
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    return FloodEligibilityEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )


def test_baseline_household_is_eligible_for_evacuation() -> None:
    result = evaluate_baseline()

    assert result.outcome == "ELIGIBLE_FOR_EVACUATION"
    assert result.eligible
    assert not result.blocked
    assert not result.pending_verification
    assert result.readiness_outcome == "READY_FOR_EVACUATION"
    assert result.failed_conditions == ()
    assert result.unknown_conditions == ()
    assert len(result.conditions) == 9


def test_eligibility_decision_is_deterministic() -> None:
    assert evaluate_baseline() == evaluate_baseline()


def test_expired_plan_authority_produces_ineligible_result() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        authority_valid_until="2026-07-25T08:00:00Z",
    )

    result = FloodEligibilityEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "INELIGIBLE"
    assert result.blocked
    assert not result.eligible
    assert result.readiness_outcome == "BLOCKED"
    assert "PLAN_AUTHORITY_CURRENT" in result.failed_conditions


def test_closed_route_produces_ineligible_result() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    route = world.get_object("RTE-000001")

    world.registry._objects["RTE-000001"] = replace(
        route,
        viability_status="CLOSED",
    )

    result = FloodEligibilityEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "INELIGIBLE"
    assert "ROUTE_AVAILABLE" in result.failed_conditions


def test_missing_assignment_produces_pending_verification() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        shelter_assignment_ids=(),
    )

    result = FloodEligibilityEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "PENDING_VERIFICATION"
    assert result.pending_verification
    assert not result.eligible
    assert not result.blocked
    assert result.readiness_outcome == "INSUFFICIENT_EVIDENCE"
    assert (
        "SHELTER_ASSIGNMENT_READY"
        in result.unknown_conditions
    )


def test_eligibility_preserves_readiness_evidence() -> None:
    result = evaluate_baseline()

    condition_evidence = tuple(
        evidence_id
        for condition in result.conditions
        for evidence_id in condition.evidence_ids
    )

    assert result.evidence_ids == condition_evidence
    assert result.evidence_ids