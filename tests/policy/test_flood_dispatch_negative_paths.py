"""Negative-path policy matrix for flood dispatch decisions."""

from dataclasses import replace

import pytest

from src.flood import (
    FloodDispatchDecisionEngine,
    SyntheticFloodWorldBuilder,
)


DECIDED_AT = "2026-07-25T08:30:00Z"


def dispatch(world):
    return FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )


@pytest.mark.parametrize(
    (
        "case_id",
        "mutator",
        "expected_decision",
        "expected_condition",
    ),
    (
        (
            "AUTHORITY_EXPIRED",
            lambda world: world.registry._objects.__setitem__(
                "FRP-000001",
                replace(
                    world.get_object("FRP-000001"),
                    authority_valid_until="2026-07-25T08:00:00Z",
                ),
            ),
            "BLOCKED",
            "DECISION_WITHIN_AUTHORITY",
        ),
        (
            "PLAN_SUPERSEDED",
            lambda world: world.registry._objects.__setitem__(
                "FRP-000001",
                replace(
                    world.get_object("FRP-000001"),
                    plan_status="SUPERSEDED",
                    superseded_by="FRP-000002",
                ),
            ),
            "SUPERSEDED",
            "PLAN_NOT_SUPERSEDED",
        ),
        (
            "ROUTE_CLOSED",
            lambda world: world.registry._objects.__setitem__(
                "RTE-000001",
                replace(
                    world.get_object("RTE-000001"),
                    viability_status="CLOSED",
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "TRANSPORT_UNREADY",
            lambda world: world.registry._objects.__setitem__(
                "TRN-000001",
                replace(
                    world.get_object("TRN-000001"),
                    readiness_status="UNAVAILABLE",
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "TRANSPORT_CAPACITY_INSUFFICIENT",
            lambda world: world.registry._objects.__setitem__(
                "TRN-000001",
                replace(
                    world.get_object("TRN-000001"),
                    capacity=2,
                    accessible_capacity=1,
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "ACCESSIBLE_TRANSPORT_MISSING",
            lambda world: world.registry._objects.__setitem__(
                "TRN-000001",
                replace(
                    world.get_object("TRN-000001"),
                    accessible_capacity=0,
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "SHELTER_AUTHORITY_INVALID",
            lambda world: world.registry._objects.__setitem__(
                "SHA-000001",
                replace(
                    world.get_object("SHA-000001"),
                    intake_authority_status="EXPIRED",
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "MATERIAL_CHANGE_DETECTED",
            lambda world: world.registry._objects.__setitem__(
                "FLI-000001",
                replace(
                    world.get_object("FLI-000001"),
                    material_change_detected=True,
                ),
            ),
            "BLOCKED",
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "HOUSEHOLD_ALREADY_EVACUATED",
            lambda world: world.registry._objects.__setitem__(
                "HHD-000001",
                replace(
                    world.get_object("HHD-000001"),
                    evacuation_status="COMPLETED",
                ),
            ),
            "BLOCKED",
            "HOUSEHOLD_AWAITS_EVACUATION",
        ),
    ),
)
def test_known_failures_block_or_supersede_dispatch(
    case_id,
    mutator,
    expected_decision,
    expected_condition,
) -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    mutator(world)

    result = dispatch(world)

    assert result.decision == expected_decision, case_id
    assert result.valid_until is None, case_id
    assert expected_condition in result.failed_conditions, case_id
    assert result.unknown_conditions == (), case_id


@pytest.mark.parametrize(
    ("case_id", "mutator", "expected_unknown_condition"),
    (
        (
            "PLAN_AUTHORITY_MISSING",
            lambda world: world.registry._objects.__setitem__(
                "FRP-000001",
                replace(
                    world.get_object("FRP-000001"),
                    authority_valid_until=None,
                ),
            ),
            "DECISION_WITHIN_AUTHORITY",
        ),
        (
            "SHELTER_ASSIGNMENT_MISSING",
            lambda world: world.registry._objects.__setitem__(
                "FRP-000001",
                replace(
                    world.get_object("FRP-000001"),
                    shelter_assignment_ids=(),
                ),
            ),
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "EVACUATION_ORDER_VALIDITY_MISSING",
            lambda world: world.registry._objects.__setitem__(
                "EVO-000001",
                replace(
                    world.get_object("EVO-000001"),
                    valid_until=None,
                ),
            ),
            "ELIGIBILITY_ESTABLISHED",
        ),
        (
            "PLAN_STATUS_UNKNOWN",
            lambda world: world.registry._objects.__setitem__(
                "FRP-000001",
                replace(
                    world.get_object("FRP-000001"),
                    plan_status="UNKNOWN",
                ),
            ),
            "PLAN_AUTHORIZED",
        ),
    ),
)
def test_unknown_state_produces_insufficient_evidence(
    case_id,
    mutator,
    expected_unknown_condition,
) -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    mutator(world)

    result = dispatch(world)

    assert result.decision == "INSUFFICIENT_EVIDENCE", case_id
    assert result.valid_until is None, case_id
    assert expected_unknown_condition in result.unknown_conditions, case_id


def test_negative_matrix_is_deterministic() -> None:
    first_world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    second_world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    first_route = first_world.get_object("RTE-000001")
    second_route = second_world.get_object("RTE-000001")

    first_world.registry._objects["RTE-000001"] = replace(
        first_route,
        viability_status="CLOSED",
    )
    second_world.registry._objects["RTE-000001"] = replace(
        second_route,
        viability_status="CLOSED",
    )

    assert dispatch(first_world) == dispatch(second_world)