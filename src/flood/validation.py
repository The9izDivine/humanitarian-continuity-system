"""Flood model-to-schema mapping and validation."""

from __future__ import annotations

from dataclasses import dataclass

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
from src.validation import SchemaRegistry, ValidationResult


FLOOD_SCHEMA_BY_TYPE: dict[
    type[CanonicalFloodObject],
    str,
] = {
    FloodIncident: "flood_incident",
    FloodZone: "flood_zone",
    Household: "flood_household",
    EvacuationOrder: "flood_evacuation_order",
    WaterLevelObservation: "flood_water_level_observation",
    RouteStatus: "flood_route_status",
    TransportationAsset: "flood_transportation_asset",
    ShelterAssignment: "flood_shelter_assignment",
    FloodResponsePlan: "flood_response_plan",
}


@dataclass(frozen=True)
class FloodSchemaValidation:
    """Schema validation result for one flood object."""

    object_id: str
    schema_name: str
    result: ValidationResult


def schema_name_for(
    item: CanonicalFloodObject,
) -> str:
    """Return the governed schema name for a flood object."""

    try:
        return FLOOD_SCHEMA_BY_TYPE[type(item)]
    except KeyError as exc:
        raise ValueError(
            f"No flood schema registered for {type(item).__name__}."
        ) from exc


def validate_flood_object(
    schemas: SchemaRegistry,
    item: CanonicalFloodObject,
) -> FloodSchemaValidation:
    """Validate one canonical flood object."""

    schema_name = schema_name_for(item)
    result = schemas.validate(schema_name, item.to_dict())

    return FloodSchemaValidation(
        object_id=item.object_id,
        schema_name=schema_name,
        result=result,
    )