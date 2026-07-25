from src.eligibility import VolunteerEligibilityEngine
from src.evidence import EvidenceLedger, EvidenceRecord


def append_readiness_evidence(
    ledger: EvidenceLedger,
    volunteer_id: str,
    *,
    training_status: str = "VALID",
    credential_status: str = "NOT_REQUIRED",
    background_check_status: str = "SATISFIED",
    availability: str = "AVAILABLE",
    contactability: str = "CONFIRMED",
    supervisor_authorization: str = "VALID",
    conflicting_assignment: bool = False,
    fatigue_status: str = "ACCEPTABLE",
) -> None:
    values = {
        "training_status": training_status,
        "credential_status": credential_status,
        "background_check_status": background_check_status,
        "availability": availability,
        "contactability": contactability,
        "supervisor_authorization": supervisor_authorization,
        "conflicting_assignment": conflicting_assignment,
        "fatigue_status": fatigue_status,
    }

    for index, (property_name, value) in enumerate(
        values.items(),
        start=1,
    ):
        ledger.append(
            EvidenceRecord(
                evidence_id=f"EV-{index:06d}",
                object_id=volunteer_id,
                property_name=property_name,
                observed_value=value,
                observed_at="2026-07-25T01:20:00Z",
                source="synthetic_test",
                verification_state="VERIFIED",
                confidence=1.0,
            )
        )


def test_fully_ready_volunteer_is_eligible() -> None:
    ledger = EvidenceLedger()
    append_readiness_evidence(ledger, "VOL-000001")

    result = VolunteerEligibilityEngine().evaluate(
        volunteer_id="VOL-000001",
        role="DUTY_OFFICER",
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "ELIGIBLE"
    assert result.failed_conditions == ()
    assert result.unknown_conditions == ()
    assert len(result.evidence_ids) == 8


def test_expired_training_blocks_eligibility() -> None:
    ledger = EvidenceLedger()
    append_readiness_evidence(
        ledger,
        "VOL-000001",
        training_status="EXPIRED",
    )

    result = VolunteerEligibilityEngine().evaluate(
        volunteer_id="VOL-000001",
        role="DUTY_OFFICER",
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "EXPIRED"
    assert result.failed_conditions == ("TRAINING_STATUS",)


def test_unavailable_volunteer_is_unavailable() -> None:
    ledger = EvidenceLedger()
    append_readiness_evidence(
        ledger,
        "VOL-000001",
        availability="UNAVAILABLE",
    )

    result = VolunteerEligibilityEngine().evaluate(
        volunteer_id="VOL-000001",
        role="DUTY_OFFICER",
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "UNAVAILABLE"
    assert result.failed_conditions == ("AVAILABILITY",)


def test_missing_evidence_requires_verification() -> None:
    ledger = EvidenceLedger()

    result = VolunteerEligibilityEngine().evaluate(
        volunteer_id="VOL-000001",
        role="DUTY_OFFICER",
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "PENDING_VERIFICATION"
    assert len(result.unknown_conditions) == 8