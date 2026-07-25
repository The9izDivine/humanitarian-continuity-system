"""Canonical flood dispatch-decision models."""

from __future__ import annotations

from dataclasses import dataclass

from src.flood.eligibility_models import FloodEligibilityDecision


@dataclass(frozen=True)
class FloodDispatchCondition:
    """Evaluation of one mandatory flood dispatch condition."""

    condition_id: str
    satisfied: bool | None
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class FloodDispatchDecision:
    """Complete governed flood evacuation dispatch decision."""

    decision_id: str
    plan_id: str
    household_id: str
    incident_id: str
    decision: str
    policy_id: str
    policy_version: str
    decided_at: str
    valid_until: str | None
    eligibility: FloodEligibilityDecision
    conditions: tuple[FloodDispatchCondition, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str

    @property
    def cleared(self) -> bool:
        """Return whether dispatch was affirmatively authorized."""

        return self.decision == "CLEARED_FOR_DISPATCH"