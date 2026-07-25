"""JSON Schema loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


class SchemaValidationError(ValueError):
    """Raised when an object fails schema validation."""


class SchemaRegistryError(ValueError):
    """Raised when schema loading or registration fails."""


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic schema validation issue."""

    path: str
    message: str
    validator: str


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for one object."""

    schema_name: str
    valid: bool
    issues: tuple[ValidationIssue, ...]


class SchemaRegistry:
    """Load and validate repository JSON Schemas."""

    def __init__(self, schema_directory: Path | str = "schemas") -> None:
        self.schema_directory = Path(schema_directory)
        self._schemas: dict[str, dict[str, Any]] = {}
        self._validators: dict[str, Draft202012Validator] = {}

    def load(self) -> None:
        """Load all JSON schemas from the configured directory."""

        if not self.schema_directory.exists():
            raise SchemaRegistryError(
                f"Schema directory not found: {self.schema_directory}"
            )

        schema_files = sorted(self.schema_directory.glob("*.schema.json"))

        if not schema_files:
            raise SchemaRegistryError("No schema files were found.")

        for schema_file in schema_files:
            try:
                schema = json.loads(
                    schema_file.read_text(encoding="utf-8")
                )
                Draft202012Validator.check_schema(schema)
            except (json.JSONDecodeError, SchemaError) as exc:
                raise SchemaRegistryError(
                    f"Invalid schema: {schema_file.name}"
                ) from exc

            schema_name = schema_file.name.removesuffix(".schema.json")
            self._schemas[schema_name] = schema
            self._validators[schema_name] = Draft202012Validator(schema)

    def schema_names(self) -> tuple[str, ...]:
        """Return registered schema names in deterministic order."""

        return tuple(sorted(self._schemas))

    def has_schema(self, schema_name: str) -> bool:
        """Return whether a schema is registered."""

        return schema_name in self._validators

    def validate(
        self,
        schema_name: str,
        payload: dict[str, Any],
    ) -> ValidationResult:
        """Validate one payload without mutating it."""

        if schema_name not in self._validators:
            raise SchemaRegistryError(
                f"Schema is not registered: {schema_name}"
            )

        validator = self._validators[schema_name]
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                error.message,
            ),
        )

        issues = tuple(
            ValidationIssue(
                path=self._format_path(error.absolute_path),
                message=error.message,
                validator=str(error.validator),
            )
            for error in errors
        )

        return ValidationResult(
            schema_name=schema_name,
            valid=not issues,
            issues=issues,
        )

    def validate_or_raise(
        self,
        schema_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Validate one payload and fail closed on any issue."""

        result = self.validate(schema_name, payload)

        if result.valid:
            return

        details = "; ".join(
            f"{issue.path}: {issue.message}"
            for issue in result.issues
        )

        raise SchemaValidationError(
            f"{schema_name} validation failed: {details}"
        )

    @staticmethod
    def _format_path(parts: Any) -> str:
        path_parts = [str(part) for part in parts]

        if not path_parts:
            return "$"

        return "$." + ".".join(path_parts)