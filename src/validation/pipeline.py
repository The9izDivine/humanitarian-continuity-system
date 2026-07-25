"""Canonical world-schema validation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.scenario import SyntheticWorld
from src.validation.schemas import (
    SchemaRegistry,
    ValidationResult,
)


class ValidationPipelineError(ValueError):
    """Raised when a world cannot be validated deterministically."""


@dataclass(frozen=True)
class ObjectValidation:
    """Validation result for one registered object."""

    object_id: str
    schema_name: str
    result: ValidationResult


@dataclass(frozen=True)
class WorldValidationReport:
    """Complete schema-validation report for one synthetic world."""

    scenario_id: str
    valid: bool
    objects: tuple[ObjectValidation, ...]
    skipped_object_ids: tuple[str, ...]


class WorldValidationPipeline:
    """Validate all schema-governed objects in a synthetic world."""

    SCHEMA_BY_PREFIX: dict[str, str] = {
        "INC": "incident",
        "VOL": "volunteer",
        "RES": "resource",
        "PLAN": "response_plan",
        "NA": "needs_assessment",
        "DEL": "delivery_record",
        "RC": "recovery_case",
        "DEC": "dispatch_decision",
    }

    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry

    def validate(self, world: SyntheticWorld) -> WorldValidationReport:
        """Validate every object whose prefix has a canonical schema."""

        validations: list[ObjectValidation] = []
        skipped: list[str] = []

        for object_id in world.registry.all_ids():
            schema_name = self._schema_for_object_id(object_id)

            if schema_name is None:
                skipped.append(object_id)
                continue

            payload = world.get_object(object_id)
            result = self.registry.validate(schema_name, payload)

            validations.append(
                ObjectValidation(
                    object_id=object_id,
                    schema_name=schema_name,
                    result=result,
                )
            )

        return WorldValidationReport(
            scenario_id=world.scenario_id,
            valid=all(item.result.valid for item in validations),
            objects=tuple(validations),
            skipped_object_ids=tuple(sorted(skipped)),
        )

    @classmethod
    def _schema_for_object_id(cls, object_id: str) -> str | None:
        prefix = object_id.split("-", maxsplit=1)[0]
        return cls.SCHEMA_BY_PREFIX.get(prefix)