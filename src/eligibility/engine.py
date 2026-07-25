"""Evidence-driven volunteer eligibility policy engine."""

from __future__ import annotations

from datetime import datetime

from src.eligibility.models import (
    ConditionEvaluation,
    EligibilityResult,
)
from src.evidence import EvidenceLedger


POLICY_ID = "HCS-POL-ELIGIBILITY-001"
POLICY_VERSION = "1.0.0"


class EligibilityEvaluationError(ValueError):
    """Raised when volunteer eligibility cannot be evaluated safely."""


class VolunteerEligibilityEngine:
    """Evaluate volunteer readiness using current evidence."""

    REQUIRED_PROPERTIES = (
        "training_status",
        "credential_status",
        "background_check_status",
        "availability",
        "contactability",
        "supervisor_authorization",
        "conflicting_assignment",
        "fatigue_status",
    )

    def evaluate(
        self,
        *,
        volunteer_id: str,
        role: str,
        ledger: EvidenceLedger,
        evaluated_at: str,
    ) -> EligibilityResult:
        """Evaluate one volunteer for one role at one time."""

        self._validate_timestamp(evaluated_at)

        conditions: list[ConditionEvaluation] = []

        for property_name in self.REQUIRED_PROPERTIES:
            evidence = ledger.current_for_property(
                volunteer_id,
                property_name,
            )

            if evidence is None:
                conditions.append(
                    ConditionEvaluation(
                        condition_id=property_name.upper(),
                        satisfied=None,
                        evidence_ids=(),
                        explanation=(
                            f"No current evidence exists for "
                            f"{property_name}."
                        ),
                    )
                )
                continue

            satisfied = self._evaluate_property(
                property_name,
                evidence.observed_value,
            )

            conditions.append(
                ConditionEvaluation(
                    condition_id=property_name.upper(),
                    satisfied=satisfied,
                    evidence_ids=(evidence.evidence_id,),
                    explanation=(
                        f"{property_name} evaluated as "
                        f"{evidence.observed_value!r}."
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
            evidence_id
            for condition in conditions
            for evidence_id in condition.evidence_ids
        )

        outcome = self._determine_outcome(
            conditions=conditions,
            failed=failed,
            unknown=unknown,
        )

        explanation = self._build_explanation(
            volunteer_id=volunteer_id,
            outcome=outcome,
            failed=failed,
            unknown=unknown,
        )

        return EligibilityResult(
            volunteer_id=volunteer_id,
            role=role,
            outcome=outcome,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            evaluated_at=evaluated_at,
            conditions=tuple(conditions),
            failed_conditions=failed,
            unknown_conditions=unknown,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _evaluate_property(
        property_name: str,
        value: object,
    ) -> bool | None:
        if property_name == "training_status":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"VALID"},
                invalid={"EXPIRED", "MISSING"},
            )

        if property_name == "credential_status":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"VALID", "NOT_REQUIRED"},
                invalid={"EXPIRED", "MISSING"},
            )

        if property_name == "background_check_status":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"SATISFIED", "NOT_REQUIRED"},
                invalid={"FAILED"},
            )

        if property_name == "availability":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"AVAILABLE"},
                invalid={"UNAVAILABLE"},
            )

        if property_name == "contactability":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"CONFIRMED"},
                invalid={"UNREACHABLE"},
            )

        if property_name == "supervisor_authorization":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"VALID", "NOT_REQUIRED"},
                invalid={"EXPIRED", "MISSING"},
            )

        if property_name == "conflicting_assignment":
            if value is False:
                return True
            if value is True:
                return False
            return None

        if property_name == "fatigue_status":
            return VolunteerEligibilityEngine._status_match(
                value,
                valid={"ACCEPTABLE"},
                invalid={"BLOCKED"},
            )

        raise EligibilityEvaluationError(
            f"Unsupported eligibility property: {property_name}"
        )

    @staticmethod
    def _status_match(
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
    def _determine_outcome(
        *,
        conditions: list[ConditionEvaluation],
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
    ) -> str:
        if failed:
            values = {
                condition.condition_id: condition.explanation
                for condition in conditions
            }

            if "TRAINING_STATUS" in failed:
                return "EXPIRED"

            if "AVAILABILITY" in failed:
                return "UNAVAILABLE"

            return "INELIGIBLE"

        if unknown:
            return "PENDING_VERIFICATION"

        return "ELIGIBLE"

    @staticmethod
    def _build_explanation(
        *,
        volunteer_id: str,
        outcome: str,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
    ) -> str:
        if failed:
            return (
                f"Volunteer {volunteer_id} is {outcome}; "
                f"failed conditions: {', '.join(failed)}."
            )

        if unknown:
            return (
                f"Volunteer {volunteer_id} is {outcome}; "
                f"unknown conditions: {', '.join(unknown)}."
            )

        return (
            f"Volunteer {volunteer_id} is ELIGIBLE; "
            "all mandatory readiness conditions are satisfied."
        )

    @staticmethod
    def _validate_timestamp(value: str) -> None:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EligibilityEvaluationError(
                f"Invalid evaluation timestamp: {value}"
            ) from exc