"""Governed registry and cross-reference validation for flood objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

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


class FloodRegistryError(ValueError):
    """Raised when registry integrity cannot be preserved."""


class FloodReferenceError(FloodRegistryError):
    """Raised when a flood-object reference is missing or invalid."""


FLOOD_MODEL_TYPES = (
    FloodIncident,
    FloodZone,
    Household,
    EvacuationOrder,
    WaterLevelObservation,
    RouteStatus,
    TransportationAsset,
    ShelterAssignment,
    FloodResponsePlan,
)


@dataclass(frozen=True)
class FloodReferenceValidation:
    """Result of validating one flood registry."""

    valid: bool
    object_count: int
    reference_count: int
    errors: tuple[str, ...]


class FloodObjectRegistry:
    """Canonical in-memory registry for flood-domain objects."""

    def __init__(self) -> None:
        self._objects: dict[str, CanonicalFloodObject] = {}

    def register(self, item: CanonicalFloodObject) -> None:
        """Register one object while preserving identity uniqueness."""

        if not isinstance(item, FLOOD_MODEL_TYPES):
            raise FloodRegistryError(
                f"Unsupported flood object type: {type(item).__name__}"
            )

        if item.object_id in self._objects:
            raise FloodRegistryError(
                f"Duplicate flood object identifier: {item.object_id}"
            )

        self._objects[item.object_id] = item

    def register_many(
        self,
        items: Iterable[CanonicalFloodObject],
    ) -> None:
        """Register multiple objects in supplied deterministic order."""

        for item in items:
            self.register(item)

    def contains(self, object_id: str) -> bool:
        """Return whether an identifier is registered."""

        return object_id in self._objects

    def get(self, object_id: str) -> CanonicalFloodObject:
        """Return one object or fail closed when it is missing."""

        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise FloodRegistryError(
                f"Flood object not found: {object_id}"
            ) from exc

    def get_as(
        self,
        object_id: str,
        expected_type: type[CanonicalFloodObject],
    ) -> CanonicalFloodObject:
        """Return an object only when its canonical type matches."""

        item = self.get(object_id)

        if not isinstance(item, expected_type):
            raise FloodRegistryError(
                f"{object_id} is {type(item).__name__}; "
                f"expected {expected_type.__name__}."
            )

        return item

    def snapshot(self) -> tuple[CanonicalFloodObject, ...]:
        """Return objects sorted by canonical identifier."""

        return tuple(
            self._objects[object_id]
            for object_id in sorted(self._objects)
        )

    def identifiers(self) -> tuple[str, ...]:
        """Return registered identifiers in deterministic order."""

        return tuple(sorted(self._objects))

    def validate_references(self) -> FloodReferenceValidation:
        """Validate all governed internal cross-references."""

        errors: list[str] = []
        reference_count = 0

        def require(
            source_id: str,
            target_id: str,
            expected_type: type[CanonicalFloodObject],
            field_name: str,
        ) -> None:
            nonlocal reference_count
            reference_count += 1

            if target_id not in self._objects:
                errors.append(
                    f"{source_id}.{field_name} references missing "
                    f"object {target_id}."
                )
                return

            target = self._objects[target_id]

            if not isinstance(target, expected_type):
                errors.append(
                    f"{source_id}.{field_name} references "
                    f"{type(target).__name__} {target_id}; expected "
                    f"{expected_type.__name__}."
                )

        for item in self.snapshot():
            if isinstance(item, FloodIncident):
                for zone_id in item.affected_zone_ids:
                    require(
                        item.object_id,
                        zone_id,
                        FloodZone,
                        "affected_zone_ids",
                    )

            elif isinstance(item, FloodZone):
                require(
                    item.object_id,
                    item.incident_id,
                    FloodIncident,
                    "incident_id",
                )

            elif isinstance(item, Household):
                require(
                    item.object_id,
                    item.zone_id,
                    FloodZone,
                    "zone_id",
                )

            elif isinstance(item, EvacuationOrder):
                require(
                    item.object_id,
                    item.incident_id,
                    FloodIncident,
                    "incident_id",
                )
                require(
                    item.object_id,
                    item.zone_id,
                    FloodZone,
                    "zone_id",
                )

                if item.superseded_by is not None:
                    require(
                        item.object_id,
                        item.superseded_by,
                        EvacuationOrder,
                        "superseded_by",
                    )

            elif isinstance(item, WaterLevelObservation):
                require(
                    item.object_id,
                    item.incident_id,
                    FloodIncident,
                    "incident_id",
                )
                require(
                    item.object_id,
                    item.zone_id,
                    FloodZone,
                    "zone_id",
                )

            elif isinstance(item, RouteStatus):
                require(
                    item.object_id,
                    item.zone_id,
                    FloodZone,
                    "zone_id",
                )

            elif isinstance(item, TransportationAsset):
                if item.assigned_plan_id is not None:
                    require(
                        item.object_id,
                        item.assigned_plan_id,
                        FloodResponsePlan,
                        "assigned_plan_id",
                    )

            elif isinstance(item, ShelterAssignment):
                require(
                    item.object_id,
                    item.household_id,
                    Household,
                    "household_id",
                )

            elif isinstance(item, FloodResponsePlan):
                require(
                    item.object_id,
                    item.incident_id,
                    FloodIncident,
                    "incident_id",
                )

                for zone_id in item.zone_ids:
                    require(
                        item.object_id,
                        zone_id,
                        FloodZone,
                        "zone_ids",
                    )

                for order_id in item.evacuation_order_ids:
                    require(
                        item.object_id,
                        order_id,
                        EvacuationOrder,
                        "evacuation_order_ids",
                    )

                for route_id in item.route_ids:
                    require(
                        item.object_id,
                        route_id,
                        RouteStatus,
                        "route_ids",
                    )

                for asset_id in item.transportation_asset_ids:
                    require(
                        item.object_id,
                        asset_id,
                        TransportationAsset,
                        "transportation_asset_ids",
                    )

                for assignment_id in item.shelter_assignment_ids:
                    require(
                        item.object_id,
                        assignment_id,
                        ShelterAssignment,
                        "shelter_assignment_ids",
                    )

                if item.superseded_by is not None:
                    require(
                        item.object_id,
                        item.superseded_by,
                        FloodResponsePlan,
                        "superseded_by",
                    )

        return FloodReferenceValidation(
            valid=not errors,
            object_count=len(self._objects),
            reference_count=reference_count,
            errors=tuple(errors),
        )

    def assert_valid_references(self) -> FloodReferenceValidation:
        """Validate references and fail closed when any error exists."""

        result = self.validate_references()

        if not result.valid:
            raise FloodReferenceError(
                "Flood registry reference validation failed: "
                + " | ".join(result.errors)
            )

        return result