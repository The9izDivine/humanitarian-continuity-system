"""Evidence-driven resource-readiness policy engine."""

from __future__ import annotations

from datetime import datetime

from src.evidence import EvidenceLedger
from src.resources.models import (
    ResourceConditionEvaluation,
    ResourceReadinessResult,
)


POLICY_ID = "HCS-POL-RESOURCE-001"
POLICY_VERSION = "1.0.0"


class ResourceEvaluationError(ValueError):
    """Raised when resource readiness cannot be evaluated safely."""


class ResourceReadinessEngine:
    """Evaluate whether a resource is currently deployable."""

    REQUIRED_PROPERTIES = (
        "quantity_verified",
        "reserved_quantity",
        "condition",
        "verification_status",
        "transport_required",
        "transport_available",
    )

    def evaluate(
        self,
        *,
        resource_id: str,
        requested_quantity: float,
        ledger: EvidenceLedger,
        evaluated_at: str,
    ) -> ResourceReadinessResult:
        """Evaluate one resource for a requested quantity."""

        self._validate_timestamp(evaluated_at)

        if requested_quantity < 0:
            raise ResourceEvaluationError(
                "Requested quantity cannot be negative."
            )

        evidence_by_property = {
            property_name: ledger.current_for_property(
                resource_id,
                property_name,
            )
            for property_name in self.REQUIRED_PROPERTIES
        }

        conditions: list[ResourceConditionEvaluation] = []

        verified_quantity = self._number_value(
            evidence_by_property["quantity_verified"]
        )
        reserved_quantity = self._number_value(
            evidence_by_property["reserved_quantity"]
        )

        available_quantity: float | None = None

        if verified_quantity is not None and reserved_quantity is not None:
            available_quantity = max(
                verified_quantity - reserved_quantity,
                0.0,
            )

        quantity_satisfied: bool | None

        if available_quantity is None:
            quantity_satisfied = None
        else:
            quantity_satisfied = available_quantity >= requested_quantity

        conditions.append(
            self._condition(
                condition_id="QUANTITY_AVAILABLE",
                satisfied=quantity_satisfied,
                evidence_records=(
                    evidence_by_property["quantity_verified"],
                    evidence_by_property["reserved_quantity"],
                ),
                explanation=(
                    "Verified and reserved quantities evaluated against "
                    f"requested quantity {requested_quantity}."
                ),
            )
        )

        condition_value = self._raw_value(
            evidence_by_property["condition"]
        )
        condition_satisfied = self._status_match(
            condition_value,
            valid={"ACCEPTABLE"},
            invalid={"DAMAGED", "EXPIRED"},
        )

        conditions.append(
            self._condition(
                condition_id="CONDITION_ACCEPTABLE",
                satisfied=condition_satisfied,
                evidence_records=(
                    evidence_by_property["condition"],
                ),
                explanation=f"Resource condition evaluated as {condition_value!r}.",
            )
        )

        verification_value = self._raw_value(
            evidence_by_property["verification_status"]
        )
        verification_satisfied = self._status_match(
            verification_value,
            valid={"AVAILABLE", "AVAILABLE_WITH_CONDITIONS"},
            invalid={
                "RESERVED",
                "UNVERIFIED",
                "DAMAGED",
                "EXPIRED",
                "DEPLETED",
                "INACCESSIBLE",
            },
        )

        conditions.append(
            self._condition(
                condition_id="VERIFICATION_CURRENT",
                satisfied=verification_satisfied,
                evidence_records=(
                    evidence_by_property["verification_status"],
                ),
                explanation=(
                    "Resource verification status evaluated as "
                    f"{verification_value!r}."
                ),
            )
        )

        transport_required = self._raw_value(
            evidence_by_property["transport_required"]
        )
        transport_available = self._raw_value(
            evidence_by_property["transport_available"]
        )

        if transport_required is False:
            transport_satisfied: bool | None = True
        elif transport_required is True:
            if transport_available is True:
                transport_satisfied = True
            elif transport_available is False:
                transport_satisfied = False
            else:
                transport_satisfied = None
        else:
            transport_satisfied = None

        conditions.append(
            self._condition(
                condition_id="TRANSPORT_AVAILABLE",
                satisfied=transport_satisfied,
                evidence_records=(
                    evidence_by_property["transport_required"],
                    evidence_by_property["transport_available"],
                ),
                explanation=(
                    f"transport_required={transport_required!r}; "
                    f"transport_available={transport_available!r}."
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

        depletion_ratio, depletion_status = self._depletion(
            requested_quantity=requested_quantity,
            available_quantity=available_quantity,
        )

        outcome = self._determine_outcome(
            failed=failed,
            unknown=unknown,
            condition_value=condition_value,
            verification_value=verification_value,
            depletion_status=depletion_status,
        )

        explanation = self._build_explanation(
            resource_id=resource_id,
            outcome=outcome,
            failed=failed,
            unknown=unknown,
            depletion_status=depletion_status,
        )

        return ResourceReadinessResult(
            resource_id=resource_id,
            outcome=outcome,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            evaluated_at=evaluated_at,
            requested_quantity=requested_quantity,
            verified_quantity=verified_quantity,
            reserved_quantity=reserved_quantity,
            available_quantity=available_quantity,
            depletion_ratio=depletion_ratio,
            depletion_status=depletion_status,
            conditions=tuple(conditions),
            failed_conditions=failed,
            unknown_conditions=unknown,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _condition(
        *,
        condition_id: str,
        satisfied: bool | None,
        evidence_records: tuple[object | None, ...],
        explanation: str,
    ) -> ResourceConditionEvaluation:
        evidence_ids = tuple(
            record.evidence_id
            for record in evidence_records
            if record is not None
        )

        return ResourceConditionEvaluation(
            condition_id=condition_id,
            satisfied=satisfied,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _raw_value(record: object | None) -> object | None:
        if record is None:
            return None

        return record.observed_value

    @classmethod
    def _number_value(cls, record: object | None) -> float | None:
        value = cls._raw_value(record)

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            return float(value)

        return None

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
    def _depletion(
        *,
        requested_quantity: float,
        available_quantity: float | None,
    ) -> tuple[float | None, str]:
        if available_quantity is None:
            return None, "UNKNOWN"

        if available_quantity == 0:
            if requested_quantity == 0:
                return 0.0, "DEPLETED"

            return None, "OVERCOMMITTED"

        ratio = requested_quantity / available_quantity

        if ratio <= 0.49:
            return ratio, "STABLE"

        if ratio <= 0.74:
            return ratio, "ELEVATED"

        if ratio <= 0.89:
            return ratio, "CRITICAL"

        if ratio <= 1.00:
            return ratio, "EXHAUSTION_IMMINENT"

        return ratio, "OVERCOMMITTED"

    @staticmethod
    def _determine_outcome(
        *,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
        condition_value: object,
        verification_value: object,
        depletion_status: str,
    ) -> str:
        if condition_value == "DAMAGED":
            return "DAMAGED"

        if condition_value == "EXPIRED":
            return "EXPIRED"

        if verification_value == "INACCESSIBLE":
            return "INACCESSIBLE"

        if depletion_status == "OVERCOMMITTED":
            return "DEPLETED"

        if failed:
            return "DEPLETED"

        if unknown:
            return "UNVERIFIED"

        if depletion_status in {
            "ELEVATED",
            "CRITICAL",
            "EXHAUSTION_IMMINENT",
        }:
            return "AVAILABLE_WITH_CONDITIONS"

        return "AVAILABLE"

    @staticmethod
    def _build_explanation(
        *,
        resource_id: str,
        outcome: str,
        failed: tuple[str, ...],
        unknown: tuple[str, ...],
        depletion_status: str,
    ) -> str:
        if failed:
            return (
                f"Resource {resource_id} is {outcome}; "
                f"failed conditions: {', '.join(failed)}; "
                f"depletion status: {depletion_status}."
            )

        if unknown:
            return (
                f"Resource {resource_id} is {outcome}; "
                f"unknown conditions: {', '.join(unknown)}."
            )

        return (
            f"Resource {resource_id} is {outcome}; "
            f"depletion status: {depletion_status}."
        )

    @staticmethod
    def _validate_timestamp(value: str) -> None:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ResourceEvaluationError(
                f"Invalid evaluation timestamp: {value}"
            ) from exc