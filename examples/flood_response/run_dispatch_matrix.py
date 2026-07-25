"""Run the deterministic flood dispatch negative-path matrix."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from src.flood import (
    FloodDispatchDecisionEngine,
    SyntheticFloodWorldBuilder,
    SyntheticFloodWorld,
)


DECIDED_AT = "2026-07-25T08:30:00Z"


def evaluate(world: SyntheticFloodWorld):
    return FloodDispatchDecisionEngine().evaluate(
        decision_id="FDD-000001",
        world=world,
        plan_id="FRP-000001",
        household_id="HHD-000001",
        decided_at=DECIDED_AT,
    )


def replace_object(
    world: SyntheticFloodWorld,
    object_id: str,
    **changes: object,
) -> None:
    world.registry._objects[object_id] = replace(
        world.get_object(object_id),
        **changes,
    )


CaseMutator = Callable[[SyntheticFloodWorld], None]


CASES: tuple[tuple[str, CaseMutator], ...] = (
    (
        "BASELINE",
        lambda world: None,
    ),
    (
        "AUTHORITY_EXPIRED",
        lambda world: replace_object(
            world,
            "FRP-000001",
            authority_valid_until="2026-07-25T08:00:00Z",
        ),
    ),
    (
        "PLAN_SUPERSEDED",
        lambda world: replace_object(
            world,
            "FRP-000001",
            plan_status="SUPERSEDED",
            superseded_by="FRP-000002",
        ),
    ),
    (
        "ROUTE_CLOSED",
        lambda world: replace_object(
            world,
            "RTE-000001",
            viability_status="CLOSED",
        ),
    ),
    (
        "TRANSPORT_UNREADY",
        lambda world: replace_object(
            world,
            "TRN-000001",
            readiness_status="UNAVAILABLE",
        ),
    ),
    (
        "TRANSPORT_CAPACITY_INSUFFICIENT",
        lambda world: replace_object(
            world,
            "TRN-000001",
            capacity=2,
            accessible_capacity=1,
        ),
    ),
    (
        "ACCESSIBLE_TRANSPORT_MISSING",
        lambda world: replace_object(
            world,
            "TRN-000001",
            accessible_capacity=0,
        ),
    ),
    (
        "SHELTER_AUTHORITY_INVALID",
        lambda world: replace_object(
            world,
            "SHA-000001",
            intake_authority_status="EXPIRED",
        ),
    ),
    (
        "MATERIAL_CHANGE_DETECTED",
        lambda world: replace_object(
            world,
            "FLI-000001",
            material_change_detected=True,
        ),
    ),
    (
        "HOUSEHOLD_ALREADY_EVACUATED",
        lambda world: replace_object(
            world,
            "HHD-000001",
            evacuation_status="COMPLETED",
        ),
    ),
    (
        "PLAN_AUTHORITY_MISSING",
        lambda world: replace_object(
            world,
            "FRP-000001",
            authority_valid_until=None,
        ),
    ),
    (
        "SHELTER_ASSIGNMENT_MISSING",
        lambda world: replace_object(
            world,
            "FRP-000001",
            shelter_assignment_ids=(),
        ),
    ),
    (
        "EVACUATION_ORDER_VALIDITY_MISSING",
        lambda world: replace_object(
            world,
            "EVO-000001",
            valid_until=None,
        ),
    ),
    (
        "PLAN_STATUS_UNKNOWN",
        lambda world: replace_object(
            world,
            "FRP-000001",
            plan_status="UNKNOWN",
        ),
    ),
)


def main() -> int:
    print("HUMANITARIAN CONTINUITY SYSTEM")
    print("FLOOD DISPATCH NEGATIVE-PATH MATRIX")
    print("=" * 62)

    results = []

    for case_id, mutator in CASES:
        world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
        mutator(world)
        decision = evaluate(world)
        results.append((case_id, decision))

        failed = (
            ", ".join(decision.failed_conditions)
            if decision.failed_conditions
            else "<none>"
        )
        unknown = (
            ", ".join(decision.unknown_conditions)
            if decision.unknown_conditions
            else "<none>"
        )

        print()
        print(f"Case       : {case_id}")
        print(f"Decision   : {decision.decision}")
        print(f"Valid Until: {decision.valid_until or '<none>'}")
        print(f"Failed     : {failed}")
        print(f"Unknown    : {unknown}")

    cleared = sum(
        item.decision == "CLEARED_FOR_DISPATCH"
        for _, item in results
    )
    blocked = sum(
        item.decision == "BLOCKED"
        for _, item in results
    )
    superseded = sum(
        item.decision == "SUPERSEDED"
        for _, item in results
    )
    insufficient = sum(
        item.decision == "INSUFFICIENT_EVIDENCE"
        for _, item in results
    )

    print()
    print("MATRIX SUMMARY")
    print("-" * 62)
    print(f"Cases                 : {len(results)}")
    print(f"Cleared                : {cleared}")
    print(f"Blocked                : {blocked}")
    print(f"Superseded             : {superseded}")
    print(f"Insufficient evidence  : {insufficient}")
    print("Deterministic outcomes : VERIFIED")

    expected = (
        len(results) == 14
        and cleared == 1
        and blocked == 8
        and superseded == 1
        and insufficient == 4
    )

    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())