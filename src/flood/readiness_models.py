"""Deterministic flood evacuation readiness results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FloodReadinessCondition:
    """One governed flood-readiness condition."""

    condition_id: str
    satisfied: bool | None
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class FloodReadinessResult:
    """Complete readiness result for one flood-response plan."""

    plan_id: str
    incident_id: str
    outcome: str
    policy_id: str
    policy_version: str
    evaluated_at: str
    conditions: tuple[FloodReadinessCondition, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str

    @property
    def ready(self) -> bool:
        """Return whether all mandatory readiness conditions passed."""

        return self.outcome == "READY_FOR_EVACUATION"