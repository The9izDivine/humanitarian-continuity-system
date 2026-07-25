from src.scenario import SyntheticWorldBuilder


def test_world_registry_and_evidence_are_connected() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()

    incident = world.get_object("INC-000001")
    incident_evidence = world.evidence.for_object("INC-000001")

    assert incident["incident_type"] == "RESIDENTIAL_FIRE"
    assert len(incident_evidence) == 1
    assert incident_evidence[0].property_name == "verification_status"
    assert incident_evidence[0].observed_value == "PARTIALLY_VERIFIED"


def test_response_plan_references_registered_objects() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()
    plan = world.get_object("PLAN-000001")

    referenced_ids = (
        plan["assigned_volunteer_ids"]
        + plan["assigned_resource_ids"]
        + [plan["incident_id"]]
    )

    assert all(
        world.registry.contains(object_id)
        for object_id in referenced_ids
    )