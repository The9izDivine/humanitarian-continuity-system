import pytest

from src.flood import (
    EvacuationOrder,
    FloodIncident,
    FloodObjectRegistry,
    FloodReferenceError,
    FloodRegistryError,
    FloodResponsePlan,
    FloodZone,
    Household,
    RouteStatus,
    ShelterAssignment,
    TransportationAsset,
    WaterLevelObservation,
)


def common(object_id: str) -> dict[str, object]:
    return {
        "object_id": object_id,
        "lifecycle_state": "CURRENT",
        "authority_source": "SYNTHETIC_AUTHORITY",
        "evidence_ids": (),
        "recorded_at": "2026-07-25T08:00:00Z",
    }


def complete_objects() -> tuple[object, ...]:
    incident = FloodIncident(
        **common("FLI-000001"),
        incident_type="FLOOD",
        severity="SEVERE",
        verification_status="VERIFIED",
        affected_zone_ids=("FLZ-000001",),
        material_change_detected=False,
    )
    zone = FloodZone(
        **common("FLZ-000001"),
        incident_id="FLI-000001",
        zone_name="Synthetic River District",
        hazard_level="HIGH",
        evacuation_required=True,
        accessibility_constraints=(),
    )
    household = Household(
        **common("HHD-000001"),
        zone_id="FLZ-000001",
        household_size=3,
        mobility_support_required=False,
        transport_required=True,
        evacuation_status="PENDING",
    )
    order = EvacuationOrder(
        **common("EVO-000001"),
        incident_id="FLI-000001",
        zone_id="FLZ-000001",
        order_status="ACTIVE",
        issued_at="2026-07-25T08:05:00Z",
        valid_until="2026-07-25T10:00:00Z",
        superseded_by=None,
    )
    observation = WaterLevelObservation(
        **common("WLO-000001"),
        incident_id="FLI-000001",
        zone_id="FLZ-000001",
        level_meters=2.4,
        trend="RISING",
        verification_state="VERIFIED",
        observed_at="2026-07-25T08:10:00Z",
    )
    route = RouteStatus(
        **common("RTE-000001"),
        zone_id="FLZ-000001",
        route_name="Synthetic Route Alpha",
        viability_status="OPEN",
        accessible_transport_supported=True,
        capacity_per_hour=120,
        last_verified_at="2026-07-25T08:12:00Z",
    )
    asset = TransportationAsset(
        **common("TRN-000001"),
        asset_type="BUS",
        capacity=20,
        accessible_capacity=4,
        readiness_status="READY",
        assigned_plan_id="FRP-000001",
    )
    assignment = ShelterAssignment(
        **common("SHA-000001"),
        household_id="HHD-000001",
        shelter_id="SHL-000001",
        assignment_status="RESERVED",
        accessible_space_required=False,
        intake_authority_status="VALID",
        completed_at=None,
    )
    plan = FloodResponsePlan(
        **common("FRP-000001"),
        incident_id="FLI-000001",
        zone_ids=("FLZ-000001",),
        evacuation_order_ids=("EVO-000001",),
        route_ids=("RTE-000001",),
        transportation_asset_ids=("TRN-000001",),
        shelter_assignment_ids=("SHA-000001",),
        plan_status="AUTHORIZED",
        authority_valid_until="2026-07-25T10:00:00Z",
        superseded_by=None,
    )

    return (
        incident,
        zone,
        household,
        order,
        observation,
        route,
        asset,
        assignment,
        plan,
    )


def test_complete_registry_references_are_valid() -> None:
    registry = FloodObjectRegistry()
    registry.register_many(complete_objects())

    result = registry.assert_valid_references()

    assert result.valid
    assert result.object_count == 9
    assert result.reference_count == 16
    assert result.errors == ()


def test_registry_snapshot_is_identifier_sorted() -> None:
    registry = FloodObjectRegistry()
    registry.register_many(reversed(complete_objects()))

    assert registry.identifiers() == tuple(
        sorted(item.object_id for item in complete_objects())
    )


def test_duplicate_identifier_fails_closed() -> None:
    registry = FloodObjectRegistry()
    incident = complete_objects()[0]

    registry.register(incident)

    with pytest.raises(FloodRegistryError):
        registry.register(incident)


def test_missing_reference_is_preserved_as_error() -> None:
    registry = FloodObjectRegistry()

    zone = FloodZone(
        **common("FLZ-000001"),
        incident_id="FLI-999999",
        zone_name="Unlinked Zone",
        hazard_level="HIGH",
        evacuation_required=True,
        accessibility_constraints=(),
    )

    registry.register(zone)

    result = registry.validate_references()

    assert not result.valid
    assert result.reference_count == 1
    assert "FLI-999999" in result.errors[0]

    with pytest.raises(FloodReferenceError):
        registry.assert_valid_references()


def test_wrong_reference_type_fails_validation() -> None:
    registry = FloodObjectRegistry()

    incident = FloodIncident(
        **common("FLI-000001"),
        incident_type="FLOOD",
        severity="SEVERE",
        verification_status="VERIFIED",
        affected_zone_ids=("FLZ-000001",),
        material_change_detected=False,
    )

    false_zone = Household(
        **common("HHD-000001"),
        zone_id="FLZ-999999",
        household_size=1,
        mobility_support_required=False,
        transport_required=False,
        evacuation_status="PENDING",
    )

    registry.register(incident)

    # Deliberately place a valid Household instance behind the zone key
    # to verify that cross-reference validation detects type corruption.
    registry._objects["FLZ-000001"] = false_zone

    result = registry.validate_references()

    assert not result.valid
    assert any(
        "expected FloodZone" in error
        for error in result.errors
    )