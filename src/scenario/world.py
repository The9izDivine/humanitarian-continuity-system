"""Synthetic humanitarian world model."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from src.evidence import EvidenceLedger, EvidenceRecord
from src.identifiers import IdentifierGenerator
from src.registry import ObjectRegistry


class SyntheticWorldError(ValueError):
    """Raised when synthetic-world construction fails."""


@dataclass
class SyntheticWorld:
    """Deterministic container for synthetic humanitarian objects."""

    scenario_id: str
    seed: int
    registry: ObjectRegistry = field(default_factory=ObjectRegistry)
    evidence: EvidenceLedger = field(default_factory=EvidenceLedger)

    def register_object(
        self,
        object_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Register a synthetic object."""

        self.registry.register(object_id, payload)

    def append_evidence(self, record: EvidenceRecord) -> None:
        """Append evidence to the world ledger."""

        self.evidence.append(record)

    def get_object(self, object_id: str) -> dict[str, Any]:
        """Return one registered object."""

        return self.registry.get(object_id)

    def snapshot(self) -> dict[str, Any]:
        """Return a deterministic defensive world snapshot."""

        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "objects": self.registry.snapshot(),
            "evidence": [
                {
                    "evidence_id": record.evidence_id,
                    "object_id": record.object_id,
                    "property_name": record.property_name,
                    "observed_value": deepcopy(record.observed_value),
                    "observed_at": record.observed_at,
                    "source": record.source,
                    "verification_state": record.verification_state,
                    "confidence": record.confidence,
                    "superseded_by": record.superseded_by,
                }
                for record in self.evidence.snapshot()
            ],
        }


@dataclass
class SyntheticWorldBuilder:
    """Build deterministic synthetic humanitarian worlds."""

    seed: int = 1
    identifiers: IdentifierGenerator = field(
        default_factory=IdentifierGenerator
    )

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise SyntheticWorldError("Seed must be zero or greater.")

    def residential_fire_world(self) -> SyntheticWorld:
        """Build the canonical residential-fire demonstration world."""

        world = SyntheticWorld(
            scenario_id="SCENARIO-RESIDENTIAL-FIRE-001",
            seed=self.seed,
        )

        incident_id = self.identifiers.next("incident")
        household_id = self.identifiers.next("household")
        volunteer_1_id = self.identifiers.next("volunteer")
        volunteer_2_id = self.identifiers.next("volunteer")
        resource_1_id = self.identifiers.next("resource")
        resource_2_id = self.identifiers.next("resource")
        plan_id = self.identifiers.next("plan")

        incident = {
            "schema_version": "1.0.0",
            "incident_id": incident_id,
            "reported_at": "2026-07-25T01:15:00Z",
            "reported_by": "SYNTHETIC-DISPATCH-SOURCE",
            "incident_type": "RESIDENTIAL_FIRE",
            "location": {
                "general_area": "Fort Worth demonstration area",
                "jurisdiction": "Synthetic jurisdiction",
                "exact_address_prohibited": True,
            },
            "estimated_households": 1,
            "estimated_people": 4,
            "known_injuries": 0,
            "immediate_hazards": [
                "STRUCTURE_FIRE",
                "SMOKE",
            ],
            "source": "synthetic_scenario_generator",
            "confidence": 0.85,
            "verification_status": "PARTIALLY_VERIFIED",
            "data_classification": "PUBLIC_SYNTHETIC",
            "notes": "Fabricated demonstration incident.",
        }

        household = {
            "household_id": household_id,
            "incident_id": incident_id,
            "estimated_adults": 2,
            "estimated_children": 2,
            "needs": [
                "SAFE_SHELTER",
                "FOOD_AND_WATER",
                "CLOTHING",
                "TRANSPORTATION",
            ],
            "data_classification": "PUBLIC_SYNTHETIC",
        }

        volunteer_1 = {
            "schema_version": "1.0.0",
            "volunteer_id": volunteer_1_id,
            "role": "DUTY_OFFICER",
            "training_status": "VALID",
            "credential_status": "NOT_REQUIRED",
            "background_check_status": "SATISFIED",
            "availability": "AVAILABLE",
            "contactability": "CONFIRMED",
            "supervisor_authorization": "VALID",
            "conflicting_assignment": False,
            "fatigue_status": "ACCEPTABLE",
            "last_verified_at": "2026-07-25T01:10:00Z",
            "data_classification": "PUBLIC_SYNTHETIC",
        }

        volunteer_2 = {
            "schema_version": "1.0.0",
            "volunteer_id": volunteer_2_id,
            "role": "RESPONSE_TEAM_MEMBER",
            "training_status": "VALID",
            "credential_status": "NOT_REQUIRED",
            "background_check_status": "SATISFIED",
            "availability": "AVAILABLE",
            "contactability": "CONFIRMED",
            "supervisor_authorization": "VALID",
            "conflicting_assignment": False,
            "fatigue_status": "ACCEPTABLE",
            "last_verified_at": "2026-07-25T01:10:00Z",
            "data_classification": "PUBLIC_SYNTHETIC",
        }

        lodging_resource = {
            "schema_version": "1.0.0",
            "resource_id": resource_1_id,
            "resource_type": "TEMPORARY_LODGING_ALLOCATION",
            "quantity_recorded": 4,
            "quantity_verified": 4,
            "reserved_quantity": 0,
            "available_quantity": 4,
            "condition": "ACCEPTABLE",
            "storage_location": "Synthetic service inventory",
            "custodian": "Synthetic resource coordinator",
            "transport_required": False,
            "transport_available": True,
            "last_inspected_at": "2026-07-25T00:45:00Z",
            "verification_status": "AVAILABLE",
            "data_classification": "PUBLIC_SYNTHETIC",
        }

        supply_resource = {
            "schema_version": "1.0.0",
            "resource_id": resource_2_id,
            "resource_type": "IMMEDIATE_NEEDS_KIT",
            "quantity_recorded": 10,
            "quantity_verified": 10,
            "reserved_quantity": 2,
            "available_quantity": 8,
            "condition": "ACCEPTABLE",
            "storage_location": "Synthetic supply facility",
            "custodian": "Synthetic resource coordinator",
            "transport_required": True,
            "transport_available": True,
            "last_inspected_at": "2026-07-25T00:45:00Z",
            "verification_status": "AVAILABLE",
            "data_classification": "PUBLIC_SYNTHETIC",
        }

        response_plan = {
            "schema_version": "1.0.0",
            "response_plan_id": plan_id,
            "incident_id": incident_id,
            "assigned_volunteer_ids": [
                volunteer_1_id,
                volunteer_2_id,
            ],
            "assigned_resource_ids": [
                resource_1_id,
                resource_2_id,
            ],
            "required_roles": [
                "DUTY_OFFICER",
                "RESPONSE_TEAM_MEMBER",
            ],
            "objectives": [
                "Confirm household immediate needs",
                "Coordinate temporary lodging",
                "Provide immediate-needs supplies",
                "Establish recovery follow-up",
            ],
            "approving_authority": "SYNTHETIC-AUTHORITY-001",
            "authority_valid_until": "2026-07-25T02:00:00Z",
            "communications_confirmed": True,
            "transport_available": True,
            "safety_conditions_acceptable": True,
            "superseded_by": None,
            "plan_status": "AUTHORIZED",
        }

        objects = {
            incident_id: incident,
            household_id: household,
            volunteer_1_id: volunteer_1,
            volunteer_2_id: volunteer_2,
            resource_1_id: lodging_resource,
            resource_2_id: supply_resource,
            plan_id: response_plan,
        }

        for object_id, payload in objects.items():
            world.register_object(object_id, payload)

        evidence_values = (
            (
                incident_id,
                "verification_status",
                "PARTIALLY_VERIFIED",
                "VERIFIED",
            ),
            (
                volunteer_1_id,
                "training_status",
                "VALID",
                "VERIFIED",
            ),
            (
                volunteer_2_id,
                "training_status",
                "VALID",
                "VERIFIED",
            ),
            (
                resource_1_id,
                "available_quantity",
                4,
                "VERIFIED",
            ),
            (
                resource_2_id,
                "available_quantity",
                8,
                "VERIFIED",
            ),
            (
                plan_id,
                "authority_valid_until",
                "2026-07-25T02:00:00Z",
                "VERIFIED",
            ),
        )

        for object_id, property_name, value, state in evidence_values:
            evidence_id = self.identifiers.next("evidence")

            world.append_evidence(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    object_id=object_id,
                    property_name=property_name,
                    observed_value=value,
                    observed_at="2026-07-25T01:20:00Z",
                    source="synthetic_world_builder",
                    verification_state=state,
                    confidence=1.0,
                )
            )

        return world