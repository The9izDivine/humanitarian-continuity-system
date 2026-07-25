import pytest

from src.registry import (
    DuplicateObjectError,
    ObjectNotFoundError,
    ObjectRegistry,
)


def test_register_and_get_object() -> None:
    registry = ObjectRegistry()
    payload = {"incident_id": "INC-000001", "status": "REPORTED"}

    registry.register("INC-000001", payload)

    assert registry.get("INC-000001") == payload
    assert registry.count() == 1


def test_registry_returns_defensive_copy() -> None:
    registry = ObjectRegistry()
    registry.register(
        "INC-000001",
        {"incident_id": "INC-000001", "status": "REPORTED"},
    )

    retrieved = registry.get("INC-000001")
    retrieved["status"] = "VERIFIED"

    assert registry.get("INC-000001")["status"] == "REPORTED"


def test_duplicate_registration_fails() -> None:
    registry = ObjectRegistry()
    registry.register("INC-000001", {"status": "REPORTED"})

    with pytest.raises(DuplicateObjectError):
        registry.register("INC-000001", {"status": "VERIFIED"})


def test_missing_object_fails() -> None:
    registry = ObjectRegistry()

    with pytest.raises(ObjectNotFoundError):
        registry.get("INC-999999")