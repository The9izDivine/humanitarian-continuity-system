import json

import pytest

from src.flood import (
    EvacuationOrder,
    FloodIncident,
    FloodModelError,
    FloodResponsePlan,
    FloodZone,
    Household,
    RouteStatus,
    ShelterAssignment,
    TransportationAsset,
    WaterLevelObservation,
)


def base_fields(object_id: str) -> dict[str, object]:
    return {
        "object_id": object_id,
        "lifecycle_state": "CURRENT",
        "authority_source": "SYNTHETIC_AUTHORITY",
        "evidence_ids": ("EV-000101",),
        "recorded_at": "2026-07-25T08:00:00Z",
    }


def test_flood_incident_serialization_is_deterministic() -> None:
    incident = FloodIncident(
        **base_fields("FLI-000001"),
        incident_type="FLOOD",
        severity="SEVERE",
        verification_status="VERIFIED",
        affected_zone_ids=("FLZ-000001",),
        material_change_detected=False,
    )

    assert incident.to_json() == incident.to_json()
    assert json.loads(incident.to_json())["object_id"] == "FLI-000001"


def test_invalid_identifier_fails_closed() -> None:
    with pytest.raises(FloodModelError):
        FloodZone(
            **base_fields("ZONE-000001"),
            incident_id="FLI-000001",
            zone_name="Synthetic Zone",
            hazard_level="HIGH",
            evacuation_required=True,
            accessibility_constraints=(),
        )


def test_household_size_must_be_positive() -> None:
    with pytest.raises(FloodModelError):
        Household(
            **base_fields("HHD-000001"),
            zone_id="FLZ-000001",
            household_size=0,
            mobility_support_required=False,
            transport_required=True,
            evacuation_status="PENDING",
        )


def test_accessible_capacity_cannot_exceed_total() -> None:
    with pytest.raises(FloodModelError):
        TransportationAsset(
            **base_fields("TRN-000001"),
            asset_type="BUS",
            capacity=10,
            accessible_capacity=11,
            readiness_status="READY",
            assigned_plan_id=None,
        )


def test_all_nine_flood_models_construct() -> None:
    objects = (
        FloodIncident(
            **base_fields("FLI-000001"),
            incident_type="FLOOD",
            severity="SEVERE",
            verification_status="VERIFIED",
            affected_zone_ids=("FLZ-000001",),
            material_change_detected=False,
        ),
        FloodZone(
            **base_fields("FLZ-000001"),
            incident_id="FLI-000001",
            zone_name="Synthetic River District",
            hazard_level="HIGH",
            evacuation_required=True,
            accessibility_constraints=(),
        ),
        Household(
            **base_fields("HHD-000001"),
            zone_id="FLZ-000001",
            household_size=3,
            mobility_support_required=False,
            transport_required=True,
            evacuation_status="PENDING",
        ),
        EvacuationOrder(
            **base_fields("EVO-000001"),
            incident_id="FLI-000001",
            zone_id="FLZ-000001",
            order_status="ACTIVE",
            issued_at="2026-07-25T08:05:00Z",
            valid_until="2026-07-25T10:00:00Z",
            superseded_by=None,
        ),
        WaterLevelObservation(
            **base_fields("WLO-000001"),
            incident_id="FLI-000001",
            zone_id="FLZ-000001",
            level_meters=2.4,
            trend="RISING",
            verification_state="VERIFIED",
            observed_at="2026-07-25T08:10:00Z",
        ),
        RouteStatus(
            **base_fields("RTE-000001"),
            zone_id="FLZ-000001",
            route_name="Synthetic Route Alpha",
            viability_status="OPEN",
            accessible_transport_supported=True,
            capacity_per_hour=120,
            last_verified_at="2026-07-25T08:12:00Z",
        ),
        TransportationAsset(
            **base_fields("TRN-000001"),
            asset_type="BUS",
            capacity=20,
            accessible_capacity=4,
            readiness_status="READY",
            assigned_plan_id="FRP-000001",
        ),
        ShelterAssignment(
            **base_fields("SHA-000001"),
            household_id="HHD-000001",
            shelter_id="SHL-000001",
            assignment_status="RESERVED",
            accessible_space_required=False,
            intake_authority_status="VALID",
            completed_at=None,
        ),
        FloodResponsePlan(
            **base_fields("FRP-000001"),
            incident_id="FLI-000001",
            zone_ids=("FLZ-000001",),
            evacuation_order_ids=("EVO-000001",),
            route_ids=("RTE-000001",),
            transportation_asset_ids=("TRN-000001",),
            shelter_assignment_ids=("SHA-000001",),
            plan_status="AUTHORIZED",
            authority_valid_until="2026-07-25T10:00:00Z",
            superseded_by=None,
        ),
    )

    assert len(objects) == 9
    assert all(item.to_json() for item in objects)