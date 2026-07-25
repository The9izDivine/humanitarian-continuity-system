from src.flood import (
    FLOOD_SCHEMA_BY_TYPE,
    SyntheticFloodWorldBuilder,
    schema_name_for,
    validate_flood_object,
)
from src.validation import SchemaRegistry


def loaded_schemas() -> SchemaRegistry:
    schemas = SchemaRegistry("schemas")
    schemas.load()
    return schemas


def test_nine_flood_schemas_are_registered() -> None:
    schemas = loaded_schemas()

    flood_names = tuple(
        name
        for name in schemas.schema_names()
        if name.startswith("flood_")
    )

    assert len(flood_names) == 9
    assert len(FLOOD_SCHEMA_BY_TYPE) == 9


def test_every_baseline_flood_object_validates() -> None:
    schemas = loaded_schemas()
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    results = tuple(
        validate_flood_object(schemas, item)
        for item in world.objects()
    )

    assert len(results) == 9
    assert all(item.result.valid for item in results)


def test_schema_mapping_is_deterministic() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    first = tuple(
        (item.object_id, schema_name_for(item))
        for item in world.objects()
    )
    second = tuple(
        (item.object_id, schema_name_for(item))
        for item in world.objects()
    )

    assert first == second


def test_invalid_payload_fails_validation() -> None:
    schemas = loaded_schemas()
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    incident = world.get_object("FLI-000001")
    payload = incident.to_dict()
    payload["incident_type"] = "FIRE"

    result = schemas.validate("flood_incident", payload)

    assert not result.valid
    assert result.issues