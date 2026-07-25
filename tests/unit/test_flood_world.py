import pytest

from src.evidence import EvidenceRecord
from src.flood import (
    FloodIncident,
    FloodResponsePlan,
    Household,
    SyntheticFloodWorldBuilder,
    SyntheticFloodWorldError,
)


def test_builder_preserves_seed() -> None:
    assert SyntheticFloodWorldBuilder(seed=17).seed == 17


def test_builder_rejects_noninteger_seed() -> None:
    with pytest.raises(SyntheticFloodWorldError):
        SyntheticFloodWorldBuilder(seed="17")  # type: ignore[arg-type]


def test_builder_rejects_negative_seed() -> None:
    with pytest.raises(SyntheticFloodWorldError):
        SyntheticFloodWorldBuilder(seed=-1)


def test_baseline_world_contains_nine_objects_and_evidence_records() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    assert len(world.objects()) == 9
    assert world.evidence.count() == 9
    assert world.scenario_id == "SCENARIO-FLOOD-BASELINE-000001"


def test_baseline_world_references_are_valid() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    result = world.validate_references()

    assert result.valid
    assert result.object_count == 9
    assert result.reference_count == 16


def test_baseline_world_evidence_is_valid() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    result = world.assert_valid_evidence()

    assert result.valid
    assert result.object_count == 9
    assert result.evidence_count == 9
    assert result.reference_count == 9
    assert result.errors == ()


def test_every_object_evidence_identifier_resolves() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    for item in world.objects():
        assert item.evidence_ids

        for evidence_id in item.evidence_ids:
            record = world.evidence.get(evidence_id)

            assert isinstance(record, EvidenceRecord)
            assert record.object_id == item.object_id


def test_baseline_world_contains_required_objects() -> None:
    world = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    assert isinstance(world.get_object("FLI-000001"), FloodIncident)
    assert isinstance(world.get_object("HHD-000001"), Household)
    assert isinstance(world.get_object("FRP-000001"), FloodResponsePlan)


def test_baseline_world_is_deterministic() -> None:
    first = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    second = SyntheticFloodWorldBuilder(seed=1).baseline_world()

    assert first.scenario_id == second.scenario_id
    assert first.identifiers() == second.identifiers()
    assert first.evidence.snapshot() == second.evidence.snapshot()

    assert tuple(item.to_json() for item in first.objects()) == tuple(
        item.to_json()
        for item in second.objects()
    )


def test_different_seeds_change_scenario_identity_only() -> None:
    first = SyntheticFloodWorldBuilder(seed=1).baseline_world()
    second = SyntheticFloodWorldBuilder(seed=2).baseline_world()

    assert first.scenario_id != second.scenario_id
    assert first.identifiers() == second.identifiers()
    assert first.evidence.snapshot() == second.evidence.snapshot()