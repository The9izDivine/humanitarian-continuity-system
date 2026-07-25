from dataclasses import replace

from src.flood import (
    FloodReadinessEngine,
    SyntheticFloodWorldBuilder,
)


EVALUATED_AT = "2026-07-25T08:30:00Z"


def evaluate_baseline():
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    return FloodReadinessEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )


def test_baseline_world_is_ready_for_evacuation() -> None:
    result = evaluate_baseline()

    assert result.outcome == "READY_FOR_EVACUATION"
    assert result.ready
    assert result.failed_conditions == ()
    assert result.unknown_conditions == ()
    assert len(result.conditions) == 9


def test_baseline_readiness_is_deterministic() -> None:
    assert evaluate_baseline() == evaluate_baseline()


def test_expired_plan_authority_blocks_readiness() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        authority_valid_until="2026-07-25T08:00:00Z",
    )

    result = FloodReadinessEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "BLOCKED"
    assert "PLAN_AUTHORITY_CURRENT" in result.failed_conditions


def test_closed_route_blocks_readiness() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    route = world.get_object("RTE-000001")

    world.registry._objects["RTE-000001"] = replace(
        route,
        viability_status="CLOSED",
    )

    result = FloodReadinessEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "BLOCKED"
    assert "ROUTE_AVAILABLE" in result.failed_conditions


def test_missing_shelter_assignment_is_insufficient_evidence() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    plan = world.get_object("FRP-000001")

    world.registry._objects["FRP-000001"] = replace(
        plan,
        shelter_assignment_ids=(),
    )

    result = FloodReadinessEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "INSUFFICIENT_EVIDENCE"
    assert (
        "SHELTER_ASSIGNMENT_READY"
        in result.unknown_conditions
    )


def test_material_change_blocks_readiness() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    incident = world.get_object("FLI-000001")

    world.registry._objects["FLI-000001"] = replace(
        incident,
        material_change_detected=True,
    )

    result = FloodReadinessEngine().evaluate(
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        evaluated_at=EVALUATED_AT,
    )

    assert result.outcome == "BLOCKED"
    assert "NO_MATERIAL_CHANGE" in result.failed_conditions