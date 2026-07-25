from src.evidence import EvidenceLedger, EvidenceRecord
from src.resources import ResourceReadinessEngine


def append_resource_evidence(
    ledger: EvidenceLedger,
    resource_id: str,
    *,
    quantity_verified: float = 10,
    reserved_quantity: float = 2,
    condition: str = "ACCEPTABLE",
    verification_status: str = "AVAILABLE",
    transport_required: bool = True,
    transport_available: bool = True,
) -> None:
    values = {
        "quantity_verified": quantity_verified,
        "reserved_quantity": reserved_quantity,
        "condition": condition,
        "verification_status": verification_status,
        "transport_required": transport_required,
        "transport_available": transport_available,
    }

    for index, (property_name, value) in enumerate(
        values.items(),
        start=1,
    ):
        ledger.append(
            EvidenceRecord(
                evidence_id=f"EV-{index:06d}",
                object_id=resource_id,
                property_name=property_name,
                observed_value=value,
                observed_at="2026-07-25T01:20:00Z",
                source="synthetic_test",
                verification_state="VERIFIED",
                confidence=1.0,
            )
        )


def test_available_resource_passes() -> None:
    ledger = EvidenceLedger()
    append_resource_evidence(ledger, "RES-000001")

    result = ResourceReadinessEngine().evaluate(
        resource_id="RES-000001",
        requested_quantity=2,
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "AVAILABLE"
    assert result.available_quantity == 8
    assert result.depletion_ratio == 0.25
    assert result.depletion_status == "STABLE"


def test_high_depletion_is_conditional() -> None:
    ledger = EvidenceLedger()
    append_resource_evidence(ledger, "RES-000001")

    result = ResourceReadinessEngine().evaluate(
        resource_id="RES-000001",
        requested_quantity=7,
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "AVAILABLE_WITH_CONDITIONS"
    assert result.depletion_status == "CRITICAL"


def test_overcommitment_blocks_resource() -> None:
    ledger = EvidenceLedger()
    append_resource_evidence(ledger, "RES-000001")

    result = ResourceReadinessEngine().evaluate(
        resource_id="RES-000001",
        requested_quantity=9,
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "DEPLETED"
    assert result.depletion_status == "OVERCOMMITTED"
    assert "QUANTITY_AVAILABLE" in result.failed_conditions


def test_damaged_resource_is_damaged() -> None:
    ledger = EvidenceLedger()
    append_resource_evidence(
        ledger,
        "RES-000001",
        condition="DAMAGED",
    )

    result = ResourceReadinessEngine().evaluate(
        resource_id="RES-000001",
        requested_quantity=1,
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "DAMAGED"
    assert "CONDITION_ACCEPTABLE" in result.failed_conditions


def test_missing_evidence_is_unverified() -> None:
    ledger = EvidenceLedger()

    result = ResourceReadinessEngine().evaluate(
        resource_id="RES-000001",
        requested_quantity=1,
        ledger=ledger,
        evaluated_at="2026-07-25T01:25:00Z",
    )

    assert result.outcome == "UNVERIFIED"
    assert len(result.unknown_conditions) == 4