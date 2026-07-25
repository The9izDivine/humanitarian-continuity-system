"""Canonical schema-validation pipeline for synthetic flood worlds."""

from __future__ import annotations

from dataclasses import dataclass

from src.flood.validation import (
    FloodSchemaValidation,
    validate_flood_object,
)
from src.flood.world import SyntheticFloodWorld
from src.validation.schemas import SchemaRegistry


class FloodValidationPipelineError(ValueError):
    """Raised when a flood world cannot be validated deterministically."""


@dataclass(frozen=True)
class FloodWorldValidationReport:
    """Complete validation report for one synthetic flood world."""

    scenario_id: str
    valid: bool
    objects: tuple[FloodSchemaValidation, ...]
    object_reference_valid: bool
    evidence_valid: bool
    errors: tuple[str, ...]

    @property
    def validated_object_count(self) -> int:
        """Return the number of schema-validated objects."""

        return len(self.objects)

    @property
    def invalid_object_ids(self) -> tuple[str, ...]:
        """Return invalid object identifiers deterministically."""

        return tuple(
            item.object_id
            for item in self.objects
            if not item.result.valid
        )


class FloodWorldValidationPipeline:
    """Validate schema, object references, and evidence integrity."""

    def __init__(self, schemas: SchemaRegistry) -> None:
        self.schemas = schemas

    def validate(
        self,
        world: SyntheticFloodWorld,
    ) -> FloodWorldValidationReport:
        """Validate one complete synthetic flood world."""

        validations = tuple(
            validate_flood_object(self.schemas, item)
            for item in world.objects()
        )

        errors: list[str] = []

        object_reference_result = world.registry.validate_references()

        if not object_reference_result.valid:
            errors.extend(object_reference_result.errors)

        evidence_result = world.validate_evidence()

        if not evidence_result.valid:
            errors.extend(evidence_result.errors)

        for validation in validations:
            for issue in validation.result.issues:
                errors.append(
                    f"{validation.object_id} "
                    f"[{validation.schema_name}] "
                    f"{issue.path}: {issue.message}"
                )

        return FloodWorldValidationReport(
            scenario_id=world.scenario_id,
            valid=(
                all(item.result.valid for item in validations)
                and object_reference_result.valid
                and evidence_result.valid
            ),
            objects=validations,
            object_reference_valid=object_reference_result.valid,
            evidence_valid=evidence_result.valid,
            errors=tuple(errors),
        )

    def validate_or_raise(
        self,
        world: SyntheticFloodWorld,
    ) -> FloodWorldValidationReport:
        """Validate a world and fail closed when any defect exists."""

        report = self.validate(world)

        if not report.valid:
            raise FloodValidationPipelineError(
                "Flood-world validation failed: "
                + " | ".join(report.errors)
            )

        return report