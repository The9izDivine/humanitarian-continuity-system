import pytest

from src.evidence import (
    DuplicateEvidenceError,
    EvidenceError,
    EvidenceLedger,
    EvidenceNotFoundError,
    EvidenceRecord,
)


def make_record(
    evidence_id: str,
    observed_value: object,
    observed_at: str = "2026-07-25T12:00:00Z",
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        object_id="VOL-000001",
        property_name="training_status",
        observed_value=observed_value,
        observed_at=observed_at,
        source="synthetic_test",
        verification_state="VERIFIED",
        confidence=1.0,
    )


def test_append_and_get_record() -> None:
    ledger = EvidenceLedger()
    record = make_record("EV-000001", "VALID")

    ledger.append(record)

    assert ledger.get("EV-000001") == record
    assert ledger.count() == 1


def test_duplicate_evidence_fails() -> None:
    ledger = EvidenceLedger()
    record = make_record("EV-000001", "VALID")
    ledger.append(record)

    with pytest.raises(DuplicateEvidenceError):
        ledger.append(record)


def test_unknown_evidence_fails() -> None:
    ledger = EvidenceLedger()

    with pytest.raises(EvidenceNotFoundError):
        ledger.get("EV-999999")


def test_invalid_confidence_fails() -> None:
    with pytest.raises(EvidenceError):
        EvidenceRecord(
            evidence_id="EV-000001",
            object_id="VOL-000001",
            property_name="training_status",
            observed_value="VALID",
            observed_at="2026-07-25T12:00:00Z",
            source="synthetic_test",
            verification_state="VERIFIED",
            confidence=1.5,
        )


def test_current_property_uses_latest_unsuperseded_record() -> None:
    ledger = EvidenceLedger()

    ledger.append(
        make_record(
            "EV-000001",
            "VALID",
            "2026-07-25T12:00:00Z",
        )
    )
    ledger.append(
        make_record(
            "EV-000002",
            "EXPIRED",
            "2026-07-25T13:00:00Z",
        )
    )

    current = ledger.current_for_property(
        "VOL-000001",
        "training_status",
    )

    assert current is not None
    assert current.evidence_id == "EV-000002"
    assert current.observed_value == "EXPIRED"


def test_supersession_preserves_original_record() -> None:
    ledger = EvidenceLedger()

    ledger.append(make_record("EV-000001", "VALID"))
    ledger.append(
        make_record(
            "EV-000002",
            "EXPIRED",
            "2026-07-25T13:00:00Z",
        )
    )

    ledger.supersede("EV-000001", "EV-000002")

    original = ledger.get("EV-000001")

    assert original.observed_value == "VALID"
    assert original.superseded_by == "EV-000002"
    assert ledger.count() == 2