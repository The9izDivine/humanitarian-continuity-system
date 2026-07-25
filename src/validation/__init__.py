"""Validation package exports.

Schema primitives are imported eagerly. World-pipeline symbols are
loaded lazily to prevent scenario and orchestration import cycles.
"""

from __future__ import annotations

from typing import Any

from src.validation.schemas import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaValidationError,
    ValidationIssue,
    ValidationResult,
)

_PIPELINE_EXPORTS = {
    "ObjectValidation",
    "ValidationPipelineError",
    "WorldValidationPipeline",
    "WorldValidationReport",
}

__all__ = [
    "ObjectValidation",
    "SchemaRegistry",
    "SchemaRegistryError",
    "SchemaValidationError",
    "ValidationIssue",
    "ValidationPipelineError",
    "ValidationResult",
    "WorldValidationPipeline",
    "WorldValidationReport",
]


def __getattr__(name: str) -> Any:
    """Load pipeline exports only when explicitly requested."""

    if name not in _PIPELINE_EXPORTS:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    from src.validation.pipeline import (
        ObjectValidation,
        ValidationPipelineError,
        WorldValidationPipeline,
        WorldValidationReport,
    )

    exports = {
        "ObjectValidation": ObjectValidation,
        "ValidationPipelineError": ValidationPipelineError,
        "WorldValidationPipeline": WorldValidationPipeline,
        "WorldValidationReport": WorldValidationReport,
    }

    value = exports[name]
    globals()[name] = value
    return value