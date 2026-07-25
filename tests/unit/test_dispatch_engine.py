from src.dispatch import DispatchDecisionEngine
from src.eligibility.models import EligibilityResult
from src.resources.models import ResourceReadinessResult


def eligible_volunteer(
    volunteer_id: str,
    role: str,
    outcome: str = "ELIGIBLE",
) -> EligibilityResult:
    return EligibilityResult(
        volunteer_id=volunteer_id,
        role=role,
        outcome=outcome,
        policy_id="HCS-POL-ELIGIBILITY-001",
        policy_version="1.0.0",
        evaluated_at="2026-07-25T01:25:00Z",
        conditions=(),
        failed_conditions=(),
        unknown_conditions=(),
        evidence_ids=(f"EV-{volunteer_id[-6:]}",),
        explanation="Synthetic test result.",
    )


def available_resource(
    resource_id: str,
    outcome: str = "AVAILABLE",
) -> ResourceReadinessResult:
    return ResourceReadinessResult(
        resource_id=resource_id,
        outcome=outcome,
        policy_id="HCS-POL-RESOURCE-001",
        policy_version="1.0.0",
        evaluated_at="2026-07-25T01:25:00Z",
        requested_quantity=1,
        verified_quantity=10,
        reserved_quantity=0,
        available_quantity=10,
        depletion_ratio=0.1,
        depletion_status="STABLE",
        conditions=(),
        failed_conditions=(),
        unknown_conditions=(),
        evidence_ids=(f"EV-{resource_id[-6:]}",),
        explanation="Synthetic test result.",
    )


def incident() -> dict[str, object]:
    return {
        "incident_id": "INC-000001",
        "verification_status": "PARTIALLY_VERIFIED",
        "location": {
            "general_area": "Synthetic area",
        },
    }


def plan() -> dict[str, object]:
    return {
        "response_plan_id": "PLAN-000001",
        "required_roles": [
            "DUTY_OFFICER",
            "RESPONSE_TEAM_MEMBER",
        ],
        "authority_valid_until": "2026-07-25T02:00:00Z",
        "communications_confirmed": True,
        "transport_available": True,
        "safety_conditions_acceptable": True,
        "superseded_by": None,
        "plan_status": "AUTHORIZED",
    }


def test_valid_plan_is_cleared() -> None:
    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=plan(),
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(
            available_resource("RES-000001"),
        ),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "CLEARED_FOR_DISPATCH"
    assert result.failed_conditions == ()
    assert result.unknown_conditions == ()
    assert result.valid_until == "2026-07-25T02:00:00Z"


def test_expired_volunteer_blocks_dispatch() -> None:
    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=plan(),
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
                outcome="EXPIRED",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(
            available_resource("RES-000001"),
        ),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "BLOCKED"
    assert (
        "VOLUNTEERS_CURRENTLY_ELIGIBLE"
        in result.failed_conditions
    )


def test_depleted_resource_blocks_dispatch() -> None:
    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=plan(),
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(
            available_resource(
                "RES-000001",
                outcome="DEPLETED",
            ),
        ),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "BLOCKED"
    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.failed_conditions
    )


def test_expired_authority_blocks_dispatch() -> None:
    expired_plan = plan()
    expired_plan["authority_valid_until"] = (
        "2026-07-25T01:00:00Z"
    )

    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=expired_plan,
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(
            available_resource("RES-000001"),
        ),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "BLOCKED"
    assert "AUTHORITY_CURRENT" in result.failed_conditions


def test_superseded_plan_is_superseded() -> None:
    superseded_plan = plan()
    superseded_plan["superseded_by"] = "PLAN-000002"
    superseded_plan["plan_status"] = "SUPERSEDED"

    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=superseded_plan,
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(
            available_resource("RES-000001"),
        ),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "SUPERSEDED"
    assert "PLAN_NOT_SUPERSEDED" in result.failed_conditions


def test_missing_resource_evaluations_are_insufficient() -> None:
    result = DispatchDecisionEngine().evaluate(
        decision_id="DEC-000001",
        response_plan=plan(),
        incident=incident(),
        volunteer_results=(
            eligible_volunteer(
                "VOL-000001",
                "DUTY_OFFICER",
            ),
            eligible_volunteer(
                "VOL-000002",
                "RESPONSE_TEAM_MEMBER",
            ),
        ),
        resource_results=(),
        decided_at="2026-07-25T01:30:00Z",
    )

    assert result.decision == "INSUFFICIENT_EVIDENCE"
    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.unknown_conditions
    )