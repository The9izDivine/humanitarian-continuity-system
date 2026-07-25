"""Resource-overcommitment blocked dispatch scenario."""

from __future__ import annotations

from src.audit import DecisionReconstructionEngine
from src.dispatch import DispatchDecisionEngine
from src.eligibility import VolunteerEligibilityEngine
from src.resources import ResourceReadinessEngine
from src.scenario.orchestration import (
    ResidentialFireScenarioOrchestrator,
    ScenarioRunResult,
)
from src.scenario.world import SyntheticWorldBuilder
from src.validation import SchemaRegistry, WorldValidationPipeline


class ResourceOvercommitmentScenarioOrchestrator:
    """Run a response scenario whose requested supply exceeds availability."""

    def run(self) -> ScenarioRunResult:
        world = SyntheticWorldBuilder(seed=1).residential_fire_world()

        schemas = SchemaRegistry("schemas")
        schemas.load()

        validation_report = WorldValidationPipeline(schemas).validate(world)

        if not validation_report.valid:
            raise ValueError("Synthetic world failed schema validation.")

        ResidentialFireScenarioOrchestrator._append_missing_operational_evidence(
            world
        )

        volunteer_engine = VolunteerEligibilityEngine()

        volunteer_results = tuple(
            volunteer_engine.evaluate(
                volunteer_id=volunteer_id,
                role=str(world.get_object(volunteer_id)["role"]),
                ledger=world.evidence,
                evaluated_at="2026-07-25T01:25:00Z",
            )
            for volunteer_id in (
                "VOL-000001",
                "VOL-000002",
            )
        )

        resource_engine = ResourceReadinessEngine()

        resource_results = (
            resource_engine.evaluate(
                resource_id="RES-000001",
                requested_quantity=4.0,
                ledger=world.evidence,
                evaluated_at="2026-07-25T01:25:00Z",
            ),
            resource_engine.evaluate(
                resource_id="RES-000002",
                requested_quantity=9.0,
                ledger=world.evidence,
                evaluated_at="2026-07-25T01:25:00Z",
            ),
        )

        dispatch_decision = DispatchDecisionEngine().evaluate(
            decision_id="DEC-000003",
            response_plan=world.get_object("PLAN-000001"),
            incident=world.get_object("INC-000001"),
            volunteer_results=volunteer_results,
            resource_results=resource_results,
            decided_at="2026-07-25T01:30:00Z",
        )

        reconstruction_report = (
            DecisionReconstructionEngine().reconstruct(
                decision=dispatch_decision,
                ledger=world.evidence,
            )
        )

        return ScenarioRunResult(
            scenario_id=(
                "SCENARIO-RESIDENTIAL-FIRE-"
                "RESOURCE-OVERCOMMITMENT-001"
            ),
            validation_report=validation_report,
            volunteer_results=volunteer_results,
            resource_results=resource_results,
            dispatch_decision=dispatch_decision,
            reconstruction_report=reconstruction_report,
        )