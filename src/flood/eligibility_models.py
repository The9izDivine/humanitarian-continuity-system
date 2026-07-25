"""Deterministic flood evacuation eligibility results."""

from __future__ import annotations

from dataclasses import dataclass

from src.flood.readiness_models import FloodReadinessCondition


@dataclass(frozen=True)
class FloodEligibilityDecision:
    """Eligibility determination for one household and response plan."""

    household_id: str
    plan_id: str
    incident_id: str
    outcome: str
    policy_id: str
    policy_version: str
    evaluated_at: str
    readiness_outcome: str
    conditions: tuple[FloodReadinessCondition, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str

    @property
    def eligible(self) -> bool:
        """Return whether eligibility has been affirmatively established."""

        return self.outcome == "ELIGIBLE_FOR_EVACUATION"

    @property
    def blocked(self) -> bool:
        """Return whether a known failed condition blocks eligibility."""

        return self.outcome == "INELIGIBLE"

    @property
    def pending_verification(self) -> bool:
        """Return whether eligibility remains unresolved."""

        return self.outcome == "PENDING_VERIFICATION"