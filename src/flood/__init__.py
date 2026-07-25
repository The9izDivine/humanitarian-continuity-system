"""Flood-response domain exports."""

from src.flood.models import (
    CanonicalFloodObject,
    EvacuationOrder,
    FloodIncident,
    FloodModelError,
    FloodResponsePlan,
    FloodZone,
    Household,
    RouteStatus,
    ShelterAssignment,
    TransportationAsset,
    WaterLevelObservation,
)
from src.flood.registry import (
    FLOOD_MODEL_TYPES,
    FloodObjectRegistry,
    FloodReferenceError,
    FloodReferenceValidation,
    FloodRegistryError,
)
from src.flood.world import (
    FloodEvidenceValidation,
    SyntheticFloodWorld,
    SyntheticFloodWorldBuilder,
    SyntheticFloodWorldError,
)

__all__ = [
    "CanonicalFloodObject",
    "EvacuationOrder",
    "FLOOD_MODEL_TYPES",
    "FloodEvidenceValidation",
    "FloodIncident",
    "FloodModelError",
    "FloodObjectRegistry",
    "FloodReferenceError",
    "FloodReferenceValidation",
    "FloodRegistryError",
    "FloodResponsePlan",
    "FloodZone",
    "Household",
    "RouteStatus",
    "ShelterAssignment",
    "SyntheticFloodWorld",
    "SyntheticFloodWorldBuilder",
    "SyntheticFloodWorldError",
    "TransportationAsset",
    "WaterLevelObservation",
]
from src.flood.validation import (
    FLOOD_SCHEMA_BY_TYPE,
    FloodSchemaValidation,
    schema_name_for,
    validate_flood_object,
)

__all__ += [
    "FLOOD_SCHEMA_BY_TYPE",
    "FloodSchemaValidation",
    "schema_name_for",
    "validate_flood_object",
]
from src.flood.pipeline import (
    FloodValidationPipelineError,
    FloodWorldValidationPipeline,
    FloodWorldValidationReport,
)

__all__ += [
    "FloodValidationPipelineError",
    "FloodWorldValidationPipeline",
    "FloodWorldValidationReport",
]
from src.flood.readiness import (
    POLICY_ID as FLOOD_READINESS_POLICY_ID,
    POLICY_VERSION as FLOOD_READINESS_POLICY_VERSION,
    FloodReadinessEngine,
    FloodReadinessEvaluationError,
)
from src.flood.readiness_models import (
    FloodReadinessCondition,
    FloodReadinessResult,
)

__all__ += [
    "FLOOD_READINESS_POLICY_ID",
    "FLOOD_READINESS_POLICY_VERSION",
    "FloodReadinessCondition",
    "FloodReadinessEngine",
    "FloodReadinessEvaluationError",
    "FloodReadinessResult",
]
from src.flood.eligibility import (
    POLICY_ID as FLOOD_ELIGIBILITY_POLICY_ID,
    POLICY_VERSION as FLOOD_ELIGIBILITY_POLICY_VERSION,
    FloodEligibilityEngine,
    FloodEligibilityEvaluationError,
)
from src.flood.eligibility_models import FloodEligibilityDecision

__all__ += [
    "FLOOD_ELIGIBILITY_POLICY_ID",
    "FLOOD_ELIGIBILITY_POLICY_VERSION",
    "FloodEligibilityDecision",
    "FloodEligibilityEngine",
    "FloodEligibilityEvaluationError",
]