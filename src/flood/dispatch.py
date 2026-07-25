"""Governed flood evacuation dispatch decision engine."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.flood.dispatch_models import (
    FloodDispatchCondition,
    FloodDispatchDecision,
)
from src.flood.eligibility import FloodEligibilityEngine
from src.flood.models import (
    FloodResponsePlan,
    Household,
)
from src.flood.world import SyntheticFloodWorld


POLICY_ID = "HCS-POL-FLOOD-DISPATCH-001"
POLICY_VERSION = "1.0.0"
DECISION_VALIDITY_MINUTES = 30


class FloodDispatchEvaluationError(ValueError):
    """Raised when flood dispatch cannot be evaluated safely."""


class FloodDispatchDecisionEngine:
    """Issue a governed dispatch decision after eligibility evaluation."""

    def __init__(
        self,
        eligibility_engine: FloodEligibilityEngine | None = None,
    ) -> None:
        self.eligibility_engine = (
            eligibility_engine
            if eligibility_engine is not None
            else FloodEligibilityEngine()
        )

    def evaluate(
        self,
        *,
        decision_id: str,
        world: SyntheticFloodWorld,
        plan_id: str,
        household_id: str,
        decided_at: str,
    ) -> FloodDispatchDecision:
        """Evaluate whether one flood evacuation may be dispatched."""

        if not decision_id.startswith("FDD-"):
            raise FloodDispatchEvaluationError(
                "Flood dispatch decision identifier must begin with FDD-."
            )

        decision_time = self._parse_timestamp(decided_at)

        plan = world.get_object(plan_id)

        if not isinstance(plan, FloodResponsePlan):
            raise FloodDispatchEvaluationError(
                f"{plan_id} is not a FloodResponsePlan."
            )

        household = world.get_object(household_id)

        if not isinstance(household, Household):
            raise FloodDispatchEvaluationError(
                f"{household_id} is not a Household."
            )

        eligibility = self.eligibility_engine.evaluate(
            world=world,
            plan_id=plan_id,
            household_id=household_id,
            evaluated_at=decided_at,
        )

        conditions = (
            FloodDispatchCondition(
                condition_id="ELIGIBILITY_ESTABLISHED",
                satisfied=self._eligibility_state(
                    eligibility.outcome
                ),
                evidence_ids=eligibility.evidence_ids,
                explanation=(
                    "Flood eligibility outcome is "
                    f"{eligibility.outcome!r}."
                ),
            ),
            FloodDispatchCondition(
                condition_id="PLAN_AUTHORIZED",
                satisfied=self._status_state(
                    plan.plan_status,
                    valid={"AUTHORIZED"},
                    invalid={"SUPERSEDED", "REVOKED", "CANCELLED"},
                ),
                evidence_ids=plan.evidence_ids,
                explanation=(
                    f"Flood plan status is {plan.plan_status!r}."
                ),
            ),
            FloodDispatchCondition(
                condition_id="PLAN_NOT_SUPERSEDED",
                satisfied=(
                    plan.superseded_by is None
                    and plan.plan_status != "SUPERSEDED"
                ),
                evidence_ids=plan.evidence_ids,
                explanation=(
                    f"Plan superseded_by={plan.superseded_by!r}; "
                    f"status={plan.plan_status!r}."
                ),
            ),
            FloodDispatchCondition(
                condition_id="HOUSEHOLD_AWAITS_EVACUATION",
                satisfied=self._status_state(
                    household.evacuation_status,
                    valid={"PENDING", "READY"},
                    invalid={
                        "COMPLETED",
                        "CANCELLED",
                        "DECLINED",
                    },
                ),
                evidence_ids=household.evidence_ids,
                explanation=(
                    "Household evacuation status is "
                    f"{household.evacuation_status!r}."
                ),
            ),
            FloodDispatchCondition(
                condition_id="DECISION_WITHIN_AUTHORITY",
                satisfied=self._authority_current(
                    plan.authority_valid_until,
                    decision_time,
                ),
                evidence_ids=plan.evidence_ids,
                explanation=(
                    "Plan authority evaluated against dispatch time; "
                    f"valid_until={plan.authority_valid_until!r}."
                ),
            ),
        )

        failed = tuple(
            condition.condition_id
            for condition in conditions
            if condition.satisfied is False
        )

        unknown = tuple(
            condition.condition_id
            for condition in conditions
            if condition.satisfied is None
        )

        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for condition in conditions
                for evidence_id in condition.evidence_ids
            )
        )

        decision = self._determine_decision(
            failed=failed,
            unknown=unknown,
        )

        valid_until = None

        if decision == "CLEARED_FOR_DISPATCH":
            valid_until = (
                decision_time
                + timedelta(minutes=DECISION_VALIDITY_MINUTES)
            ).isoformat().replace("+00:00", "Z")

        explanation = self._build_explanation(
            plan_id=plan_id,
            household_id=household_id,
            decision=decision,
            failed=failed,
            unknown=unknown,
        )

        return FloodDispatchDecision(
            decision_id=decision_id,
            plan_id=plan_id,
            household_id=household_id,
            incident_id=eligibility.incident_id,
            decision=decision,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            decided_at=decided_at,
            valid_until=valid_until,
            eligibility=eligibility,
            conditions=conditions,
            failed_conditions=failed,
            unknown_conditions=unknown,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _eligibility_state(value: str) -> bool | None:
        if value == "ELIGIBLE_FOR_EVACUATION":
            return True

        if value == "INELIGIBLE":
            return False

        if value == "PENDING_VERIFICATION":
            return None

        return None

    @staticmethod
    def _status_state(
        value: object,
        *,
        valid: set[str],
        invalid: set[str],
    ) -> bool | None:
        if value in valid:
            return True

        if value in invalid:
            return False

        return None

    @staticmethod
    def _authority_current(
        authority_valid_until: str | None,
        decision_time: datetime,
    ) -> bool | None:
        if authority_valid_until is None:
            return None

        try:
            authority_time = datetime.fromisoformat(
                authority_valid_until.replace("Z", "+00:00")
            )
        except ValueError:
            return None

        return authority_time >= decision_time

    @staticmethod
    def _determine_decision(
        *,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
    ) -> str:
        if "PLAN_NOT_SUPERSEDED" in failed:
            return "SUPERSEDED"

        if failed:
            return "BLOCKED"

        if unknown:
            return "INSUFFICIENT_EVIDENCE"

        return "CLEARED_FOR_DISPATCH"

    @staticmethod
    def _build_explanation(
        *,
        plan_id: str,
        household_id: str,
        decision: str,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
    ) -> str:
        if failed:
            return (
                f"Flood plan {plan_id} for household "
                f"{household_id} produced {decision}; "
                f"failed conditions: {', '.join(failed)}."
            )

        if unknown:
            return (
                f"Flood plan {plan_id} for household "
                f"{household_id} produced {decision}; "
                f"unknown conditions: {', '.join(unknown)}."
            )

        return (
            f"Flood plan {plan_id} for household {household_id} "
            "is CLEARED_FOR_DISPATCH; all mandatory dispatch "
            "conditions are satisfied."
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise FloodDispatchEvaluationError(
                f"Invalid dispatch timestamp: {value}"
            ) from exc