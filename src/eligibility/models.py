"""Canonical eligibility evaluation models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionEvaluation:
    """Evaluation result for one policy condition."""

    condition_id: str
    satisfied: bool | None
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class EligibilityResult:
    """Complete volunteer-eligibility evaluation."""

    volunteer_id: str
    role: str
    outcome: str
    policy_id: str
    policy_version: str
    evaluated_at: str
    conditions: tuple[ConditionEvaluation, ...]
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation: str