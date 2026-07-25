"""Canonical resource-readiness evaluation models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceConditionEvaluation:
    """Evaluation result for one resource condition."""

    condition_id: str
    satisfied: bool | None
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class ResourceReadinessResult:
    """Complete resource-readiness evaluation."""

    resource_id: str
    outcome: str
    policy_id: str
    policy_version: str
    evaluated_at: str
    requested_quantity: float
    verified_quantity: float | None
    reserved_quantity: float | None
    available_quantity: float | None
    depletion_ratio: float | None
    depletion_status: str
    conditions: tuple[ResourceConditionEvaluation, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str