"""Canonical flood-response domain models."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, ClassVar


class FloodModelError(ValueError):
    """Raised when a flood-domain object violates its contract."""


@dataclass(frozen=True)
class CanonicalFloodObject:
    """Constitutional fields shared by every flood-domain object."""

    object_id: str
    lifecycle_state: str
    authority_source: str
    evidence_ids: tuple[str, ...]
    recorded_at: str

    ID_PREFIX: ClassVar[str] = ""

    def __post_init__(self) -> None:
        for name in (
            "object_id",
            "lifecycle_state",
            "authority_source",
            "recorded_at",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise FloodModelError(
                    f"{name} must be a non-empty string."
                )

        pattern = rf"^{re.escape(self.ID_PREFIX)}-\d{{6}}$"

        if not re.fullmatch(pattern, self.object_id):
            raise FloodModelError(
                f"{type(self).__name__} identifier must match "
                f"{self.ID_PREFIX}-######."
            )

        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise FloodModelError(
                f"Duplicate evidence identifiers on {self.object_id}."
            )

        for evidence_id in self.evidence_ids:
            if not re.fullmatch(r"^EV-\d{6}$", evidence_id):
                raise FloodModelError(
                    f"Invalid evidence identifier: {evidence_id!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic dictionary representation."""

        return asdict(self)

    def to_json(self) -> str:
        """Return canonical deterministic JSON."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )


@dataclass(frozen=True)
class FloodIncident(CanonicalFloodObject):
    """Observed flood incident and current hazard state."""

    incident_type: str
    severity: str
    verification_status: str
    affected_zone_ids: tuple[str, ...]
    material_change_detected: bool

    ID_PREFIX: ClassVar[str] = "FLI"

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.incident_type != "FLOOD":
            raise FloodModelError(
                "FloodIncident incident_type must be 'FLOOD'."
            )

        if not self.affected_zone_ids:
            raise FloodModelError(
                "FloodIncident requires an affected zone."
            )


@dataclass(frozen=True)
class FloodZone(CanonicalFloodObject):
    """Governed geographic flood zone."""

    incident_id: str
    zone_name: str
    hazard_level: str
    evacuation_required: bool
    accessibility_constraints: tuple[str, ...]

    ID_PREFIX: ClassVar[str] = "FLZ"


@dataclass(frozen=True)
class Household(CanonicalFloodObject):
    """Synthetic household requiring evacuation evaluation."""

    zone_id: str
    household_size: int
    mobility_support_required: bool
    transport_required: bool
    evacuation_status: str

    ID_PREFIX: ClassVar[str] = "HHD"

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.household_size < 1:
            raise FloodModelError(
                "Household size must be at least one."
            )


@dataclass(frozen=True)
class EvacuationOrder(CanonicalFloodObject):
    """Authority governing evacuation of a flood zone."""

    incident_id: str
    zone_id: str
    order_status: str
    issued_at: str
    valid_until: str | None
    superseded_by: str | None

    ID_PREFIX: ClassVar[str] = "EVO"


@dataclass(frozen=True)
class WaterLevelObservation(CanonicalFloodObject):
    """Recorded water-level observation."""

    incident_id: str
    zone_id: str
    level_meters: float
    trend: str
    verification_state: str
    observed_at: str

    ID_PREFIX: ClassVar[str] = "WLO"

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.level_meters < 0:
            raise FloodModelError(
                "Water level cannot be negative."
            )


@dataclass(frozen=True)
class RouteStatus(CanonicalFloodObject):
    """Current evacuation-route viability."""

    zone_id: str
    route_name: str
    viability_status: str
    accessible_transport_supported: bool
    capacity_per_hour: int
    last_verified_at: str

    ID_PREFIX: ClassVar[str] = "RTE"

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.capacity_per_hour < 0:
            raise FloodModelError(
                "Route capacity cannot be negative."
            )


@dataclass(frozen=True)
class TransportationAsset(CanonicalFloodObject):
    """Transport asset available to a flood-response plan."""

    asset_type: str
    capacity: int
    accessible_capacity: int
    readiness_status: str
    assigned_plan_id: str | None

    ID_PREFIX: ClassVar[str] = "TRN"

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.capacity < 0:
            raise FloodModelError(
                "Transportation capacity cannot be negative."
            )

        if self.accessible_capacity < 0:
            raise FloodModelError(
                "Accessible capacity cannot be negative."
            )

        if self.accessible_capacity > self.capacity:
            raise FloodModelError(
                "Accessible capacity cannot exceed total capacity."
            )


@dataclass(frozen=True)
class ShelterAssignment(CanonicalFloodObject):
    """Synthetic household-to-shelter assignment."""

    household_id: str
    shelter_id: str
    assignment_status: str
    accessible_space_required: bool
    intake_authority_status: str
    completed_at: str | None

    ID_PREFIX: ClassVar[str] = "SHA"


@dataclass(frozen=True)
class FloodResponsePlan(CanonicalFloodObject):
    """Governed flood-response plan."""

    incident_id: str
    zone_ids: tuple[str, ...]
    evacuation_order_ids: tuple[str, ...]
    route_ids: tuple[str, ...]
    transportation_asset_ids: tuple[str, ...]
    shelter_assignment_ids: tuple[str, ...]
    plan_status: str
    authority_valid_until: str | None
    superseded_by: str | None

    ID_PREFIX: ClassVar[str] = "FRP"

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.zone_ids:
            raise FloodModelError(
                "FloodResponsePlan requires at least one zone."
            )

        if not self.route_ids:
            raise FloodModelError(
                "FloodResponsePlan requires at least one route."
            )