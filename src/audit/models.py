"""Canonical decision reconstruction models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconstructionCondition:
    """One reconstructed decision condition."""

    condition_id: str
    status: str
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class ReconstructionReport:
    """Complete decision reconstruction report."""

    decision_id: str
    response_plan_id: str
    incident_id: str
    decision: str
    policy_id: str
    policy_version: str
    decided_at: str
    valid_until: str | None
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    conditions: tuple[ReconstructionCondition, ...]
    summary: str
    timeline: tuple[str, ...]