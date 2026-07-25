"""End-to-end synthetic scenario orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from src.audit import (
    DecisionReconstructionEngine,
    ReconstructionReport,
)
from src.dispatch import (
    DispatchDecision,
    DispatchDecisionEngine,
)
from src.eligibility import (
    EligibilityResult,
    VolunteerEligibilityEngine,
)
from src.evidence import EvidenceLedger, EvidenceRecord
from src.resources import (
    ResourceReadinessEngine,
    ResourceReadinessResult,
)
from src.scenario.world import SyntheticWorld, SyntheticWorldBuilder
from src.validation import (
    SchemaRegistry,
    WorldValidationPipeline,
    WorldValidationReport,
)


@dataclass(frozen=True)
class ScenarioRunResult:
    """Complete end-to-end scenario result."""

    scenario_id: str
    validation_report: WorldValidationReport
    volunteer_results: tuple[EligibilityResult, ...]
    resource_results: tuple[ResourceReadinessResult, ...]
    dispatch_decision: DispatchDecision
    reconstruction_report: ReconstructionReport


class ScenarioOrchestrationError(ValueError):
    """Raised when a scenario cannot be orchestrated safely."""


class ResidentialFireScenarioOrchestrator:
    """Run the canonical residential-fire demonstration end to end."""

    def run(self) -> ScenarioRunResult:
        """Execute validation, policy evaluation, decision, and reconstruction."""

        world = SyntheticWorldBuilder(seed=1).residential_fire_world()

        validation_report = self._validate_world(world)

        if not validation_report.valid:
            raise ScenarioOrchestrationError(
                "Synthetic world failed schema validation."
            )

        self._append_missing_operational_evidence(world)

        volunteer_results = self._evaluate_volunteers(world)
        resource_results = self._evaluate_resources(world)

        response_plan = world.get_object("PLAN-000001")
        incident = world.get_object("INC-000001")

        dispatch_decision = DispatchDecisionEngine().evaluate(
            decision_id="DEC-000001",
            response_plan=response_plan,
            incident=incident,
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
            scenario_id=world.scenario_id,
            validation_report=validation_report,
            volunteer_results=volunteer_results,
            resource_results=resource_results,
            dispatch_decision=dispatch_decision,
            reconstruction_report=reconstruction_report,
        )

    @staticmethod
    def _validate_world(
        world: SyntheticWorld,
    ) -> WorldValidationReport:
        schemas = SchemaRegistry("schemas")
        schemas.load()

        return WorldValidationPipeline(schemas).validate(world)

    @staticmethod
    def _append_missing_operational_evidence(
        world: SyntheticWorld,
    ) -> None:
        values: tuple[tuple[str, str, object], ...] = (
            ("VOL-000001", "credential_status", "NOT_REQUIRED"),
            ("VOL-000001", "background_check_status", "SATISFIED"),
            ("VOL-000001", "availability", "AVAILABLE"),
            ("VOL-000001", "contactability", "CONFIRMED"),
            ("VOL-000001", "supervisor_authorization", "VALID"),
            ("VOL-000001", "conflicting_assignment", False),
            ("VOL-000001", "fatigue_status", "ACCEPTABLE"),
            ("VOL-000002", "credential_status", "NOT_REQUIRED"),
            ("VOL-000002", "background_check_status", "SATISFIED"),
            ("VOL-000002", "availability", "AVAILABLE"),
            ("VOL-000002", "contactability", "CONFIRMED"),
            ("VOL-000002", "supervisor_authorization", "VALID"),
            ("VOL-000002", "conflicting_assignment", False),
            ("VOL-000002", "fatigue_status", "ACCEPTABLE"),
            ("RES-000001", "quantity_verified", 4),
            ("RES-000001", "reserved_quantity", 0),
            ("RES-000001", "condition", "ACCEPTABLE"),
            ("RES-000001", "verification_status", "AVAILABLE"),
            ("RES-000001", "transport_required", False),
            ("RES-000001", "transport_available", True),
            ("RES-000002", "quantity_verified", 10),
            ("RES-000002", "reserved_quantity", 2),
            ("RES-000002", "condition", "ACCEPTABLE"),
            ("RES-000002", "verification_status", "AVAILABLE"),
            ("RES-000002", "transport_required", True),
            ("RES-000002", "transport_available", True),
        )

        existing_ids = {
            record.evidence_id
            for record in world.evidence.snapshot()
        }

        next_sequence = 1

        while f"EV-{next_sequence:06d}" in existing_ids:
            next_sequence += 1

        for object_id, property_name, observed_value in values:
            world.evidence.append(
                EvidenceRecord(
                    evidence_id=f"EV-{next_sequence:06d}",
                    object_id=object_id,
                    property_name=property_name,
                    observed_value=observed_value,
                    observed_at="2026-07-25T01:22:00Z",
                    source="residential_fire_orchestrator",
                    verification_state="VERIFIED",
                    confidence=1.0,
                )
            )

            next_sequence += 1

    @staticmethod
    def _evaluate_volunteers(
        world: SyntheticWorld,
    ) -> tuple[EligibilityResult, ...]:
        engine = VolunteerEligibilityEngine()

        volunteer_ids = (
            "VOL-000001",
            "VOL-000002",
        )

        results: list[EligibilityResult] = []

        for volunteer_id in volunteer_ids:
            volunteer = world.get_object(volunteer_id)

            results.append(
                engine.evaluate(
                    volunteer_id=volunteer_id,
                    role=str(volunteer["role"]),
                    ledger=world.evidence,
                    evaluated_at="2026-07-25T01:25:00Z",
                )
            )

        return tuple(results)

    @staticmethod
    def _evaluate_resources(
        world: SyntheticWorld,
    ) -> tuple[ResourceReadinessResult, ...]:
        engine = ResourceReadinessEngine()

        requests = (
            ("RES-000001", 4.0),
            ("RES-000002", 2.0),
        )

        return tuple(
            engine.evaluate(
                resource_id=resource_id,
                requested_quantity=requested_quantity,
                ledger=world.evidence,
                evaluated_at="2026-07-25T01:25:00Z",
            )
            for resource_id, requested_quantity in requests
        )