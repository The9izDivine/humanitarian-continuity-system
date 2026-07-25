import pytest

from src.audit import (
    DecisionReconstructionEngine,
    ReconstructionError,
)
from src.dispatch.models import (
    DispatchCondition,
    DispatchDecision,
)
from src.evidence import EvidenceLedger, EvidenceRecord


def decision() -> DispatchDecision:
    return DispatchDecision(
        decision_id="DEC-000001",
        response_plan_id="PLAN-000001",
        incident_id="INC-000001",
        decision="CLEARED_FOR_DISPATCH",
        policy_id="HCS-POL-DISPATCH-001",
        policy_version="1.0.0",
        decided_at="2026-07-25T01:30:00Z",
        valid_until="2026-07-25T02:00:00Z",
        conditions=(
            DispatchCondition(
                condition_id="VOLUNTEERS_CURRENTLY_ELIGIBLE",
                satisfied=True,
                evidence_ids=("EV-000001",),
                explanation="Volunteer eligibility confirmed.",
            ),
            DispatchCondition(
                condition_id="RESOURCES_CURRENTLY_AVAILABLE",
                satisfied=True,
                evidence_ids=("EV-000002",),
                explanation="Resource availability confirmed.",
            ),
        ),
        volunteer_results=(),
        resource_results=(),
        failed_conditions=(),
        unknown_conditions=(),
        evidence_ids=("EV-000001", "EV-000002"),
        explanation="All mandatory conditions satisfied.",
    )


def ledger() -> EvidenceLedger:
    evidence = EvidenceLedger()

    evidence.append(
        EvidenceRecord(
            evidence_id="EV-000001",
            object_id="VOL-000001",
            property_name="training_status",
            observed_value="VALID",
            observed_at="2026-07-25T01:20:00Z",
            source="synthetic_test",
            verification_state="VERIFIED",
            confidence=1.0,
        )
    )

    evidence.append(
        EvidenceRecord(
            evidence_id="EV-000002",
            object_id="RES-000001",
            property_name="available_quantity",
            observed_value=8,
            observed_at="2026-07-25T01:21:00Z",
            source="synthetic_test",
            verification_state="VERIFIED",
            confidence=1.0,
        )
    )

    return evidence


def test_reconstruction_preserves_decision_and_evidence() -> None:
    report = DecisionReconstructionEngine().reconstruct(
        decision=decision(),
        ledger=ledger(),
    )

    assert report.decision == "CLEARED_FOR_DISPATCH"
    assert report.evidence_ids == (
        "EV-000001",
        "EV-000002",
    )
    assert len(report.timeline) == 3
    assert report.conditions[0].status == "SATISFIED"


def test_reconstruction_text_is_deterministic() -> None:
    engine = DecisionReconstructionEngine()

    first = engine.to_text(
        engine.reconstruct(
            decision=decision(),
            ledger=ledger(),
        )
    )

    second = engine.to_text(
        engine.reconstruct(
            decision=decision(),
            ledger=ledger(),
        )
    )

    assert first == second
    assert "DECISION RECONSTRUCTION" in first
    assert "CLEARED_FOR_DISPATCH" in first


def test_missing_evidence_fails_closed() -> None:
    empty_ledger = EvidenceLedger()

    with pytest.raises(ReconstructionError):
        DecisionReconstructionEngine().reconstruct(
            decision=decision(),
            ledger=empty_ledger,
        )