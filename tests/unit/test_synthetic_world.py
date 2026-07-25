import pytest

from src.scenario import (
    SyntheticWorldBuilder,
    SyntheticWorldError,
)


def test_residential_fire_world_is_deterministic() -> None:
    first = SyntheticWorldBuilder(seed=7).residential_fire_world()
    second = SyntheticWorldBuilder(seed=7).residential_fire_world()

    assert first.snapshot() == second.snapshot()


def test_residential_fire_world_contains_expected_objects() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()

    assert world.registry.count() == 7
    assert world.evidence.count() == 6

    assert world.registry.contains("INC-000001")
    assert world.registry.contains("HH-000001")
    assert world.registry.contains("VOL-000001")
    assert world.registry.contains("VOL-000002")
    assert world.registry.contains("RES-000001")
    assert world.registry.contains("RES-000002")
    assert world.registry.contains("PLAN-000001")


def test_world_snapshot_is_defensive() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()
    snapshot = world.snapshot()

    snapshot["objects"]["INC-000001"]["verification_status"] = "CLOSED"

    assert (
        world.get_object("INC-000001")["verification_status"]
        == "PARTIALLY_VERIFIED"
    )


def test_world_uses_synthetic_data_classification() -> None:
    world = SyntheticWorldBuilder(seed=1).residential_fire_world()
    snapshot = world.snapshot()

    classifications = {
        payload["data_classification"]
        for payload in snapshot["objects"].values()
        if "data_classification" in payload
    }

    assert classifications == {"PUBLIC_SYNTHETIC"}


def test_negative_seed_fails_closed() -> None:
    with pytest.raises(SyntheticWorldError):
        SyntheticWorldBuilder(seed=-1)