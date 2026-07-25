from src.scenario import SyntheticWorldBuilder
from src.validation import (
    SchemaRegistry,
    WorldValidationPipeline,
)


def test_residential_fire_world_schema_validation() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()

    schemas = SchemaRegistry("schemas")
    schemas.load()

    report = WorldValidationPipeline(schemas).validate(world)

    assert report.valid
    assert report.scenario_id == "SCENARIO-RESIDENTIAL-FIRE-001"

    validated_ids = {
        item.object_id
        for item in report.objects
    }

    assert validated_ids == {
        "INC-000001",
        "PLAN-000001",
        "RES-000001",
        "RES-000002",
        "VOL-000001",
        "VOL-000002",
    }

    assert report.skipped_object_ids == ("HH-000001",)


def test_pipeline_detects_invalid_registered_object() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()

    invalid_incident = world.get_object("INC-000001")
    invalid_incident["incident_id"] = "BROKEN"

    world.registry._objects["INC-000001"] = invalid_incident

    schemas = SchemaRegistry("schemas")
    schemas.load()

    report = WorldValidationPipeline(schemas).validate(world)

    assert not report.valid

    incident_result = next(
        item
        for item in report.objects
        if item.object_id == "INC-000001"
    )

    assert not incident_result.result.valid