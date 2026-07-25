"""Canonical in-memory object registry."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


class RegistryError(ValueError):
    """Base registry error."""


class DuplicateObjectError(RegistryError):
    """Raised when an identifier is registered more than once."""


class ObjectNotFoundError(RegistryError):
    """Raised when an identifier cannot be found."""


@dataclass
class ObjectRegistry:
    """Store validated canonical objects by stable identifier."""

    _objects: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, object_id: str, payload: dict[str, Any]) -> None:
        """Register a new object without permitting silent replacement."""

        if not object_id or not isinstance(object_id, str):
            raise RegistryError("Object identifier must be a non-empty string.")

        if object_id in self._objects:
            raise DuplicateObjectError(
                f"Object already registered: {object_id}"
            )

        self._objects[object_id] = deepcopy(payload)

    def get(self, object_id: str) -> dict[str, Any]:
        """Return a defensive copy of a registered object."""

        if object_id not in self._objects:
            raise ObjectNotFoundError(f"Object not found: {object_id}")

        return deepcopy(self._objects[object_id])

    def contains(self, object_id: str) -> bool:
        """Return whether an object is registered."""

        return object_id in self._objects

    def all_ids(self) -> tuple[str, ...]:
        """Return registered identifiers in deterministic order."""

        return tuple(sorted(self._objects))

    def count(self) -> int:
        """Return total registered object count."""

        return len(self._objects)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a defensive snapshot of the complete registry."""

        return deepcopy(self._objects)