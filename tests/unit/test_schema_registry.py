import pytest

from src.validation import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaValidationError,
)


def test_schema_registry_loads_repository_schemas() -> None:
    registry = SchemaRegistry("schemas")
    registry.load()

    assert "incident" in registry.schema_names()
    assert "volunteer" in registry.schema_names()
    assert "resource" in registry.schema_names()
    assert "response_plan" in registry.schema_names()


def test_valid_incident_passes() -> None:
    registry = SchemaRegistry("schemas")
    registry.load()

    payload = {
        "schema_version": "1.0.0",
        "incident_id": "INC-000001",
        "reported_at": "2026-07-25T01:15:00Z",
        "incident_type": "RESIDENTIAL_FIRE",
        "location": {
            "general_area": "Synthetic area",
            "exact_address_prohibited": True,
        },
        "verification_status": "REPORTED",
        "data_classification": "PUBLIC_SYNTHETIC",
    }

    result = registry.validate("incident", payload)

    assert result.valid
    assert result.issues == ()


def test_invalid_incident_returns_deterministic_issues() -> None:
    registry = SchemaRegistry("schemas")
    registry.load()

    payload = {
        "schema_version": "1.0.0",
        "incident_id": "INVALID",
        "reported_at": "not-a-time",
        "incident_type": "RESIDENTIAL_FIRE",
        "location": {
            "general_area": "Synthetic area",
            "exact_address_prohibited": True,
        },
        "verification_status": "REPORTED",
        "data_classification": "PUBLIC_SYNTHETIC",
    }

    result = registry.validate("incident", payload)

    assert not result.valid
    assert any(
        issue.path == "$.incident_id"
        for issue in result.issues
    )


def test_validate_or_raise_fails_closed() -> None:
    registry = SchemaRegistry("schemas")
    registry.load()

    with pytest.raises(SchemaValidationError):
        registry.validate_or_raise(
            "incident",
            {"incident_id": "INC-000001"},
        )


def test_unknown_schema_fails() -> None:
    registry = SchemaRegistry("schemas")
    registry.load()

    with pytest.raises(SchemaRegistryError):
        registry.validate("unknown", {})