import json

import pytest

from src.flood import (
    FloodValidationPipelineError,
    FloodWorldValidationPipeline,
    SyntheticFloodWorldBuilder,
)
from src.validation.schemas import SchemaRegistry


def loaded_schemas() -> SchemaRegistry:
    schemas = SchemaRegistry("schemas")
    schemas.load()
    return schemas


def test_baseline_flood_world_is_fully_valid() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    pipeline = FloodWorldValidationPipeline(loaded_schemas())

    report = pipeline.validate_or_raise(world)

    assert report.valid
    assert report.scenario_id == "SCENARIO-FLOOD-BASELINE-000001"
    assert report.validated_object_count == 9
    assert report.object_reference_valid
    assert report.evidence_valid
    assert report.invalid_object_ids == ()
    assert report.errors == ()


def test_pipeline_results_are_deterministic() -> None:
    pipeline = FloodWorldValidationPipeline(loaded_schemas())

    first = pipeline.validate(
        SyntheticFloodWorldBuilder(seed=1).baseline_world()
    )
    second = pipeline.validate(
        SyntheticFloodWorldBuilder(seed=1).baseline_world()
    )

    assert first == second


def test_pipeline_preserves_schema_failures() -> None:
    schemas = loaded_schemas()
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    schema = json.loads(
        schemas.schema_directory.joinpath(
            "flood_incident.schema.json"
        ).read_text(encoding="utf-8")
    )

    schema["properties"]["severity"]["const"] = "IMPOSSIBLE_VALUE"

    from jsonschema import Draft202012Validator

    schemas._validators["flood_incident"] = Draft202012Validator(schema)

    pipeline = FloodWorldValidationPipeline(schemas)
    report = pipeline.validate(world)

    assert not report.valid
    assert report.invalid_object_ids == ("FLI-000001",)
    assert report.errors

    with pytest.raises(FloodValidationPipelineError):
        pipeline.validate_or_raise(world)


def test_all_object_schema_mappings_are_recorded() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    report = FloodWorldValidationPipeline(
        loaded_schemas()
    ).validate_or_raise(world)

    mappings = tuple(
        (item.object_id, item.schema_name)
        for item in report.objects
    )

    assert mappings == (
        ("EVO-000001", "flood_evacuation_order"),
        ("FLI-000001", "flood_incident"),
        ("FLZ-000001", "flood_zone"),
        ("FRP-000001", "flood_response_plan"),
        ("HHD-000001", "flood_household"),
        ("RTE-000001", "flood_route_status"),
        ("SHA-000001", "flood_shelter_assignment"),
        ("TRN-000001", "flood_transportation_asset"),
        ("WLO-000001", "flood_water_level_observation"),
    )