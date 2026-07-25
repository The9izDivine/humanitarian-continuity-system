"""Governed flood evacuation eligibility decision engine."""

from __future__ import annotations

from src.flood.eligibility_models import FloodEligibilityDecision
from src.flood.readiness import FloodReadinessEngine
from src.flood.world import SyntheticFloodWorld


POLICY_ID = "HCS-POL-FLOOD-ELIGIBILITY-001"
POLICY_VERSION = "1.0.0"


class FloodEligibilityEvaluationError(ValueError):
    """Raised when flood eligibility cannot be determined safely."""


class FloodEligibilityEngine:
    """Determine eligibility without authorizing operational dispatch."""

    def __init__(
        self,
        readiness_engine: FloodReadinessEngine | None = None,
    ) -> None:
        self.readiness_engine = (
            readiness_engine
            if readiness_engine is not None
            else FloodReadinessEngine()
        )

    def evaluate(
        self,
        *,
        world: SyntheticFloodWorld,
        plan_id: str,
        household_id: str,
        evaluated_at: str,
    ) -> FloodEligibilityDecision:
        """Evaluate one household against one governed flood plan."""

        readiness = self.readiness_engine.evaluate(
            world=world,
            plan_id=plan_id,
            household_id=household_id,
            evaluated_at=evaluated_at,
        )

        if readiness.outcome == "READY_FOR_EVACUATION":
            outcome = "ELIGIBLE_FOR_EVACUATION"
            explanation = (
                f"Household {household_id} is "
                "ELIGIBLE_FOR_EVACUATION under plan "
                f"{plan_id}; every mandatory readiness condition "
                "is satisfied."
            )

        elif readiness.outcome == "BLOCKED":
            outcome = "INELIGIBLE"
            explanation = (
                f"Household {household_id} is INELIGIBLE under "
                f"plan {plan_id}; failed conditions: "
                f"{', '.join(readiness.failed_conditions)}."
            )

        elif readiness.outcome == "INSUFFICIENT_EVIDENCE":
            outcome = "PENDING_VERIFICATION"
            explanation = (
                f"Household {household_id} is "
                "PENDING_VERIFICATION under plan "
                f"{plan_id}; unknown conditions: "
                f"{', '.join(readiness.unknown_conditions)}."
            )

        else:
            raise FloodEligibilityEvaluationError(
                "Unsupported flood readiness outcome: "
                f"{readiness.outcome}"
            )

        return FloodEligibilityDecision(
            household_id=household_id,
            plan_id=readiness.plan_id,
            incident_id=readiness.incident_id,
            outcome=outcome,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            evaluated_at=evaluated_at,
            readiness_outcome=readiness.outcome,
            conditions=readiness.conditions,
            failed_conditions=readiness.failed_conditions,
            unknown_conditions=readiness.unknown_conditions,
            evidence_ids=readiness.evidence_ids,
            explanation=explanation,
        )