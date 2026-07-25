"""Deterministic synthetic flood-world container and builder."""

from __future__ import annotations

from dataclasses import dataclass

from src.evidence import EvidenceLedger, EvidenceRecord
from src.flood.models import (
    CanonicalFloodObject,
    EvacuationOrder,
    FloodIncident,
    FloodResponsePlan,
    FloodZone,
    Household,
    RouteStatus,
    ShelterAssignment,
    TransportationAsset,
    WaterLevelObservation,
)
from src.flood.registry import (
    FloodObjectRegistry,
    FloodReferenceValidation,
)


class SyntheticFloodWorldError(ValueError):
    """Raised when synthetic flood-world integrity fails."""


@dataclass(frozen=True)
class FloodEvidenceValidation:
    """Result of validating object-to-evidence references."""

    valid: bool
    object_count: int
    evidence_count: int
    reference_count: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class SyntheticFloodWorld:
    """Complete deterministic synthetic flood-response world."""

    scenario_id: str
    seed: int
    registry: FloodObjectRegistry
    evidence: EvidenceLedger

    def validate_references(self) -> FloodReferenceValidation:
        """Validate every governed object cross-reference."""

        return self.registry.assert_valid_references()

    def validate_evidence(self) -> FloodEvidenceValidation:
        """Verify that all model evidence identifiers resolve."""

        errors: list[str] = []
        reference_count = 0

        for item in self.objects():
            for evidence_id in item.evidence_ids:
                reference_count += 1

                try:
                    record = self.evidence.get(evidence_id)
                except Exception:
                    errors.append(
                        f"{item.object_id} references missing "
                        f"evidence {evidence_id}."
                    )
                    continue

                if record.object_id != item.object_id:
                    errors.append(
                        f"{item.object_id} references evidence "
                        f"{evidence_id} owned by {record.object_id}."
                    )

        return FloodEvidenceValidation(
            valid=not errors,
            object_count=len(self.objects()),
            evidence_count=self.evidence.count(),
            reference_count=reference_count,
            errors=tuple(errors),
        )

    def assert_valid_evidence(self) -> FloodEvidenceValidation:
        """Fail closed when evidence integrity is not preserved."""

        result = self.validate_evidence()

        if not result.valid:
            raise SyntheticFloodWorldError(
                "Flood-world evidence validation failed: "
                + " | ".join(result.errors)
            )

        return result

    def objects(self) -> tuple[CanonicalFloodObject, ...]:
        """Return all objects in deterministic identifier order."""

        return self.registry.snapshot()

    def identifiers(self) -> tuple[str, ...]:
        """Return all identifiers in deterministic order."""

        return self.registry.identifiers()

    def get_object(
        self,
        object_id: str,
    ) -> CanonicalFloodObject:
        """Return one canonical object by identifier."""

        return self.registry.get(object_id)


class SyntheticFloodWorldBuilder:
    """Build deterministic synthetic flood-response worlds."""

    def __init__(self, seed: int = 1) -> None:
        if not isinstance(seed, int):
            raise SyntheticFloodWorldError(
                "Synthetic flood-world seed must be an integer."
            )

        if seed < 0:
            raise SyntheticFloodWorldError(
                "Synthetic flood-world seed cannot be negative."
            )

        self.seed = seed

    @staticmethod
    def _build_evidence() -> EvidenceLedger:
        ledger = EvidenceLedger()

        records = (
            EvidenceRecord(
                evidence_id="EV-000101",
                object_id="FLI-000001",
                property_name="verification_status",
                observed_value="VERIFIED",
                observed_at="2026-07-25T08:00:00Z",
                source="SYNTHETIC_INCIDENT_AUTHORITY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
            EvidenceRecord(
                evidence_id="EV-000102",
                object_id="FLZ-000001",
                property_name="hazard_level",
                observed_value="HIGH",
                observed_at="2026-07-25T08:02:00Z",
                source="SYNTHETIC_ZONE_AUTHORITY",
                verification_state="VERIFIED",
                confidence=0.98,
            ),
            EvidenceRecord(
                evidence_id="EV-000103",
                object_id="HHD-000001",
                property_name="mobility_support_required",
                observed_value=True,
                observed_at="2026-07-25T08:04:00Z",
                source="SYNTHETIC_HOUSEHOLD_REGISTRY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
            EvidenceRecord(
                evidence_id="EV-000104",
                object_id="EVO-000001",
                property_name="order_status",
                observed_value="ACTIVE",
                observed_at="2026-07-25T08:05:00Z",
                source="SYNTHETIC_EVACUATION_AUTHORITY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
            EvidenceRecord(
                evidence_id="EV-000105",
                object_id="WLO-000001",
                property_name="level_meters",
                observed_value=2.4,
                observed_at="2026-07-25T08:10:00Z",
                source="SYNTHETIC_SENSOR_NETWORK",
                verification_state="VERIFIED",
                confidence=0.97,
            ),
            EvidenceRecord(
                evidence_id="EV-000106",
                object_id="RTE-000001",
                property_name="viability_status",
                observed_value="OPEN",
                observed_at="2026-07-25T08:12:00Z",
                source="SYNTHETIC_ROUTE_AUTHORITY",
                verification_state="VERIFIED",
                confidence=0.95,
            ),
            EvidenceRecord(
                evidence_id="EV-000107",
                object_id="TRN-000001",
                property_name="readiness_status",
                observed_value="READY",
                observed_at="2026-07-25T08:14:00Z",
                source="SYNTHETIC_TRANSPORT_AUTHORITY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
            EvidenceRecord(
                evidence_id="EV-000108",
                object_id="SHA-000001",
                property_name="intake_authority_status",
                observed_value="VALID",
                observed_at="2026-07-25T08:16:00Z",
                source="SYNTHETIC_SHELTER_AUTHORITY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
            EvidenceRecord(
                evidence_id="EV-000109",
                object_id="FRP-000001",
                property_name="plan_status",
                observed_value="AUTHORIZED",
                observed_at="2026-07-25T08:20:00Z",
                source="SYNTHETIC_RESPONSE_AUTHORITY",
                verification_state="VERIFIED",
                confidence=1.0,
            ),
        )

        for record in records:
            ledger.append(record)

        return ledger

    def baseline_world(self) -> SyntheticFloodWorld:
        """Build the canonical valid flood-response baseline."""

        objects: tuple[CanonicalFloodObject, ...] = (
            FloodIncident(
                object_id="FLI-000001",
                lifecycle_state="ACTIVE",
                authority_source="SYNTHETIC_INCIDENT_AUTHORITY",
                evidence_ids=("EV-000101",),
                recorded_at="2026-07-25T08:00:00Z",
                incident_type="FLOOD",
                severity="SEVERE",
                verification_status="VERIFIED",
                affected_zone_ids=("FLZ-000001",),
                material_change_detected=False,
            ),
            FloodZone(
                object_id="FLZ-000001",
                lifecycle_state="ACTIVE",
                authority_source="SYNTHETIC_ZONE_AUTHORITY",
                evidence_ids=("EV-000102",),
                recorded_at="2026-07-25T08:02:00Z",
                incident_id="FLI-000001",
                zone_name="Synthetic River District",
                hazard_level="HIGH",
                evacuation_required=True,
                accessibility_constraints=(
                    "LOW_CLEARANCE_ROUTE",
                ),
            ),
            Household(
                object_id="HHD-000001",
                lifecycle_state="AWAITING_EVACUATION",
                authority_source="SYNTHETIC_HOUSEHOLD_REGISTRY",
                evidence_ids=("EV-000103",),
                recorded_at="2026-07-25T08:04:00Z",
                zone_id="FLZ-000001",
                household_size=3,
                mobility_support_required=True,
                transport_required=True,
                evacuation_status="PENDING",
            ),
            EvacuationOrder(
                object_id="EVO-000001",
                lifecycle_state="CURRENT",
                authority_source="SYNTHETIC_EVACUATION_AUTHORITY",
                evidence_ids=("EV-000104",),
                recorded_at="2026-07-25T08:05:00Z",
                incident_id="FLI-000001",
                zone_id="FLZ-000001",
                order_status="ACTIVE",
                issued_at="2026-07-25T08:05:00Z",
                valid_until="2026-07-25T10:00:00Z",
                superseded_by=None,
            ),
            WaterLevelObservation(
                object_id="WLO-000001",
                lifecycle_state="CURRENT",
                authority_source="SYNTHETIC_SENSOR_NETWORK",
                evidence_ids=("EV-000105",),
                recorded_at="2026-07-25T08:10:00Z",
                incident_id="FLI-000001",
                zone_id="FLZ-000001",
                level_meters=2.4,
                trend="RISING",
                verification_state="VERIFIED",
                observed_at="2026-07-25T08:10:00Z",
            ),
            RouteStatus(
                object_id="RTE-000001",
                lifecycle_state="CURRENT",
                authority_source="SYNTHETIC_ROUTE_AUTHORITY",
                evidence_ids=("EV-000106",),
                recorded_at="2026-07-25T08:12:00Z",
                zone_id="FLZ-000001",
                route_name="Synthetic Route Alpha",
                viability_status="OPEN",
                accessible_transport_supported=True,
                capacity_per_hour=120,
                last_verified_at="2026-07-25T08:12:00Z",
            ),
            TransportationAsset(
                object_id="TRN-000001",
                lifecycle_state="AVAILABLE",
                authority_source="SYNTHETIC_TRANSPORT_AUTHORITY",
                evidence_ids=("EV-000107",),
                recorded_at="2026-07-25T08:14:00Z",
                asset_type="ACCESSIBLE_BUS",
                capacity=20,
                accessible_capacity=4,
                readiness_status="READY",
                assigned_plan_id="FRP-000001",
            ),
            ShelterAssignment(
                object_id="SHA-000001",
                lifecycle_state="RESERVED",
                authority_source="SYNTHETIC_SHELTER_AUTHORITY",
                evidence_ids=("EV-000108",),
                recorded_at="2026-07-25T08:16:00Z",
                household_id="HHD-000001",
                shelter_id="SHL-000001",
                assignment_status="RESERVED",
                accessible_space_required=True,
                intake_authority_status="VALID",
                completed_at=None,
            ),
            FloodResponsePlan(
                object_id="FRP-000001",
                lifecycle_state="AUTHORIZED",
                authority_source="SYNTHETIC_RESPONSE_AUTHORITY",
                evidence_ids=("EV-000109",),
                recorded_at="2026-07-25T08:20:00Z",
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

        registry = FloodObjectRegistry()
        registry.register_many(objects)
        registry.assert_valid_references()

        world = SyntheticFloodWorld(
            scenario_id=(
                f"SCENARIO-FLOOD-BASELINE-{self.seed:06d}"
            ),
            seed=self.seed,
            registry=registry,
            evidence=self._build_evidence(),
        )

        world.assert_valid_evidence()
        return world