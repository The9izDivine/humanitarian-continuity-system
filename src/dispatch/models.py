"""Canonical dispatch-decision models."""

from __future__ import annotations

from dataclasses import dataclass

from src.eligibility.models import EligibilityResult
from src.resources.models import ResourceReadinessResult


@dataclass(frozen=True)
class DispatchCondition:
    """Evaluation of one mandatory dispatch condition."""

    condition_id: str
    satisfied: bool | None
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class DispatchDecision:
    """Complete governed dispatch decision."""

    decision_id: str
    response_plan_id: str
    incident_id: str
    decision: str
    policy_id: str
    policy_version: str
    decided_at: str
    valid_until: str | None
    conditions: tuple[DispatchCondition, ...]
    volunteer_results: tuple[EligibilityResult, ...]
    resource_results: tuple[ResourceReadinessResult, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str