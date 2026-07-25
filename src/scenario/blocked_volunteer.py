"""Expired-volunteer blocked dispatch scenario."""

from __future__ import annotations

from copy import deepcopy

from src.audit import DecisionReconstructionEngine
from src.dispatch import DispatchDecisionEngine
from src.eligibility import VolunteerEligibilityEngine
from src.evidence import EvidenceRecord
from src.resources import ResourceReadinessEngine
from src.scenario.orchestration import (
    ResidentialFireScenarioOrchestrator,
    ScenarioRunResult,
)
from src.scenario.world import SyntheticWorldBuilder
from src.validation import SchemaRegistry, WorldValidationPipeline


class BlockedVolunteerScenarioOrchestrator:
    """Run a residential-fire scenario with expired volunteer training."""

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

        expired_record = EvidenceRecord(
            evidence_id="EV-000033",
            object_id="VOL-000002",
            property_name="training_status",
            observed_value="EXPIRED",
            observed_at="2026-07-25T01:24:00Z",
            source="blocked_volunteer_scenario",
            verification_state="VERIFIED",
            confidence=1.0,
        )

        world.evidence.append(expired_record)
        world.evidence.supersede("EV-000003", "EV-000033")

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

        resource_results = tuple(
            resource_engine.evaluate(
                resource_id=resource_id,
                requested_quantity=requested_quantity,
                ledger=world.evidence,
                evaluated_at="2026-07-25T01:25:00Z",
            )
            for resource_id, requested_quantity in (
                ("RES-000001", 4.0),
                ("RES-000002", 2.0),
            )
        )

        dispatch_decision = DispatchDecisionEngine().evaluate(
            decision_id="DEC-000002",
            response_plan=deepcopy(
                world.get_object("PLAN-000001")
            ),
            incident=deepcopy(
                world.get_object("INC-000001")
            ),
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
            scenario_id="SCENARIO-RESIDENTIAL-FIRE-BLOCKED-VOLUNTEER-001",
            validation_report=validation_report,
            volunteer_results=volunteer_results,
            resource_results=resource_results,
            dispatch_decision=dispatch_decision,
            reconstruction_report=reconstruction_report,
        )