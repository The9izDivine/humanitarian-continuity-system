"""Governed dispatch-decision engine."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.dispatch.models import (
    DispatchCondition,
    DispatchDecision,
)
from src.eligibility.models import EligibilityResult
from src.resources.models import ResourceReadinessResult


POLICY_ID = "HCS-POL-DISPATCH-001"
POLICY_VERSION = "1.0.0"
DECISION_VALIDITY_MINUTES = 30


class DispatchEvaluationError(ValueError):
    """Raised when a dispatch decision cannot be evaluated safely."""


class DispatchDecisionEngine:
    """Combine current policy evaluations into one dispatch decision."""

    def evaluate(
        self,
        *,
        decision_id: str,
        response_plan: dict[str, object],
        incident: dict[str, object],
        volunteer_results: tuple[EligibilityResult, ...],
        resource_results: tuple[ResourceReadinessResult, ...],
        decided_at: str,
    ) -> DispatchDecision:
        """Evaluate whether a response plan may proceed."""

        decision_time = self._parse_timestamp(decided_at)

        response_plan_id = self._required_string(
            response_plan,
            "response_plan_id",
        )
        incident_id = self._required_string(
            incident,
            "incident_id",
        )

        conditions: list[DispatchCondition] = []

        incident_status = incident.get("verification_status")
        incident_active = incident_status in {
            "PARTIALLY_VERIFIED",
            "VERIFIED",
        }

        if incident_status is None:
            incident_active_result: bool | None = None
        else:
            incident_active_result = incident_active

        conditions.append(
            DispatchCondition(
                condition_id="INCIDENT_ACTIVE",
                satisfied=incident_active_result,
                evidence_ids=(),
                explanation=(
                    f"Incident verification status is {incident_status!r}."
                ),
            )
        )

        location = incident.get("location")

        if not isinstance(location, dict):
            location_sufficient: bool | None = None
        else:
            general_area = location.get("general_area")
            location_sufficient = bool(
                isinstance(general_area, str)
                and general_area.strip()
            )

        conditions.append(
            DispatchCondition(
                condition_id="LOCATION_SUFFICIENT",
                satisfied=location_sufficient,
                evidence_ids=(),
                explanation="Incident location sufficiency evaluated.",
            )
        )

        required_roles = response_plan.get("required_roles")

        if not isinstance(required_roles, list):
            roles_filled: bool | None = None
        else:
            evaluated_roles = {
                result.role
                for result in volunteer_results
            }
            roles_filled = set(required_roles).issubset(evaluated_roles)

        conditions.append(
            DispatchCondition(
                condition_id="REQUIRED_ROLES_FILLED",
                satisfied=roles_filled,
                evidence_ids=(),
                explanation="Required roles compared with evaluated volunteers.",
            )
        )

        volunteer_condition = self._evaluate_volunteers(
            volunteer_results
        )
        conditions.append(volunteer_condition)

        resource_condition = self._evaluate_resources(
            resource_results
        )
        conditions.append(resource_condition)

        safety_value = response_plan.get(
            "safety_conditions_acceptable"
        )
        safety_result = (
            safety_value
            if isinstance(safety_value, bool)
            else None
        )

        conditions.append(
            DispatchCondition(
                condition_id="SAFETY_CONDITIONS_ACCEPTABLE",
                satisfied=safety_result,
                evidence_ids=(),
                explanation=(
                    "Response-plan safety condition evaluated as "
                    f"{safety_value!r}."
                ),
            )
        )

        authority_until = response_plan.get("authority_valid_until")
        authority_current = self._authority_current(
            authority_until,
            decision_time,
        )

        conditions.append(
            DispatchCondition(
                condition_id="AUTHORITY_CURRENT",
                satisfied=authority_current,
                evidence_ids=(),
                explanation=(
                    "Authority validity evaluated against decision time."
                ),
            )
        )

        communications_value = response_plan.get(
            "communications_confirmed"
        )
        communications_result = (
            communications_value
            if isinstance(communications_value, bool)
            else None
        )

        conditions.append(
            DispatchCondition(
                condition_id="COMMUNICATIONS_CONFIRMED",
                satisfied=communications_result,
                evidence_ids=(),
                explanation=(
                    "Communications status evaluated as "
                    f"{communications_value!r}."
                ),
            )
        )

        transport_value = response_plan.get("transport_available")
        transport_result = (
            transport_value
            if isinstance(transport_value, bool)
            else None
        )

        conditions.append(
            DispatchCondition(
                condition_id="TRANSPORT_AVAILABLE",
                satisfied=transport_result,
                evidence_ids=(),
                explanation=(
                    "Transport availability evaluated as "
                    f"{transport_value!r}."
                ),
            )
        )

        superseded_by = response_plan.get("superseded_by")
        plan_status = response_plan.get("plan_status")

        if superseded_by:
            not_superseded = False
        elif plan_status == "SUPERSEDED":
            not_superseded = False
        elif plan_status is None:
            not_superseded = None
        else:
            not_superseded = True

        conditions.append(
            DispatchCondition(
                condition_id="PLAN_NOT_SUPERSEDED",
                satisfied=not_superseded,
                evidence_ids=(),
                explanation=(
                    f"Plan status is {plan_status!r}; "
                    f"superseded_by={superseded_by!r}."
                ),
            )
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

        if decision in {
            "CLEARED_FOR_DISPATCH",
            "CLEARED_WITH_CONDITIONS",
        }:
            valid_until = (
                decision_time
                + timedelta(minutes=DECISION_VALIDITY_MINUTES)
            ).isoformat().replace("+00:00", "Z")

        explanation = self._build_explanation(
            response_plan_id=response_plan_id,
            decision=decision,
            failed=failed,
            unknown=unknown,
        )

        return DispatchDecision(
            decision_id=decision_id,
            response_plan_id=response_plan_id,
            incident_id=incident_id,
            decision=decision,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            decided_at=decided_at,
            valid_until=valid_until,
            conditions=tuple(conditions),
            volunteer_results=volunteer_results,
            resource_results=resource_results,
            failed_conditions=failed,
            unknown_conditions=unknown,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _evaluate_volunteers(
        results: tuple[EligibilityResult, ...],
    ) -> DispatchCondition:
        if not results:
            return DispatchCondition(
                condition_id="VOLUNTEERS_CURRENTLY_ELIGIBLE",
                satisfied=None,
                evidence_ids=(),
                explanation="No volunteer evaluations were supplied.",
            )

        blocking_outcomes = {
            "INELIGIBLE",
            "EXPIRED",
            "UNAVAILABLE",
        }
        unknown_outcomes = {
            "PENDING_VERIFICATION",
            "INSUFFICIENT_INFORMATION",
        }

        if any(
            result.outcome in blocking_outcomes
            for result in results
        ):
            satisfied: bool | None = False
        elif any(
            result.outcome in unknown_outcomes
            for result in results
        ):
            satisfied = None
        else:
            satisfied = True

        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for result in results
                for evidence_id in result.evidence_ids
            )
        )

        outcomes = ", ".join(
            f"{result.volunteer_id}:{result.outcome}"
            for result in results
        )

        return DispatchCondition(
            condition_id="VOLUNTEERS_CURRENTLY_ELIGIBLE",
            satisfied=satisfied,
            evidence_ids=evidence_ids,
            explanation=f"Volunteer outcomes: {outcomes}.",
        )

    @staticmethod
    def _evaluate_resources(
        results: tuple[ResourceReadinessResult, ...],
    ) -> DispatchCondition:
        if not results:
            return DispatchCondition(
                condition_id="RESOURCES_CURRENTLY_AVAILABLE",
                satisfied=None,
                evidence_ids=(),
                explanation="No resource evaluations were supplied.",
            )

        blocking_outcomes = {
            "DEPLETED",
            "DAMAGED",
            "EXPIRED",
            "INACCESSIBLE",
        }

        if any(
            result.outcome in blocking_outcomes
            for result in results
        ):
            satisfied: bool | None = False
        elif any(
            result.outcome == "UNVERIFIED"
            for result in results
        ):
            satisfied = None
        else:
            satisfied = True

        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for result in results
                for evidence_id in result.evidence_ids
            )
        )

        outcomes = ", ".join(
            f"{result.resource_id}:{result.outcome}"
            for result in results
        )

        return DispatchCondition(
            condition_id="RESOURCES_CURRENTLY_AVAILABLE",
            satisfied=satisfied,
            evidence_ids=evidence_ids,
            explanation=f"Resource outcomes: {outcomes}.",
        )

    @staticmethod
    def _authority_current(
        authority_until: object,
        decision_time: datetime,
    ) -> bool | None:
        if not isinstance(authority_until, str):
            return None

        try:
            authority_time = datetime.fromisoformat(
                authority_until.replace("Z", "+00:00")
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
        response_plan_id: str,
        decision: str,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
    ) -> str:
        if failed:
            return (
                f"Response plan {response_plan_id} is {decision}; "
                f"failed conditions: {', '.join(failed)}."
            )

        if unknown:
            return (
                f"Response plan {response_plan_id} is {decision}; "
                f"unknown conditions: {', '.join(unknown)}."
            )

        return (
            f"Response plan {response_plan_id} is "
            "CLEARED_FOR_DISPATCH; all mandatory dispatch "
            "conditions are satisfied."
        )

    @staticmethod
    def _required_string(
        payload: dict[str, object],
        key: str,
    ) -> str:
        value = payload.get(key)

        if not isinstance(value, str) or not value.strip():
            raise DispatchEvaluationError(
                f"Required string is missing: {key}"
            )

        return value

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise DispatchEvaluationError(
                f"Invalid decision timestamp: {value}"
            ) from exc