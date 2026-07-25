"""Deterministic scenario replay and fingerprinting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

from src.scenario.orchestration import ScenarioRunResult


class ScenarioRunner(Protocol):
    """Protocol implemented by deterministic scenario orchestrators."""

    def run(self) -> ScenarioRunResult:
        """Execute and return one complete scenario result."""


class ReplayError(ValueError):
    """Raised when scenario replay integrity fails."""


@dataclass(frozen=True)
class ReplayRecord:
    """Canonical replay record for one scenario execution."""

    scenario_id: str
    fingerprint: str
    decision: str
    failed_conditions: tuple[str, ...]
    unknown_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    timeline: tuple[str, ...]


@dataclass(frozen=True)
class ReplayVerification:
    """Comparison of two deterministic scenario executions."""

    scenario_id: str
    first: ReplayRecord
    second: ReplayRecord
    deterministic: bool


class ScenarioReplayEngine:
    """Execute, fingerprint, and compare deterministic scenarios."""

    def capture(self, runner: ScenarioRunner) -> ReplayRecord:
        """Run a scenario and capture its canonical replay record."""

        result = runner.run()
        canonical = self._canonical_payload(result)
        encoded = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

        fingerprint = hashlib.sha256(encoded).hexdigest()

        return ReplayRecord(
            scenario_id=result.scenario_id,
            fingerprint=fingerprint,
            decision=result.dispatch_decision.decision,
            failed_conditions=result.dispatch_decision.failed_conditions,
            unknown_conditions=result.dispatch_decision.unknown_conditions,
            evidence_ids=result.reconstruction_report.evidence_ids,
            timeline=result.reconstruction_report.timeline,
        )

    def verify(self, runner: ScenarioRunner) -> ReplayVerification:
        """Run the same scenario twice and compare fingerprints."""

        first = self.capture(runner)
        second = self.capture(runner)

        if first.scenario_id != second.scenario_id:
            raise ReplayError(
                "Scenario identifier changed between replay executions."
            )

        return ReplayVerification(
            scenario_id=first.scenario_id,
            first=first,
            second=second,
            deterministic=first.fingerprint == second.fingerprint,
        )

    @staticmethod
    def assert_deterministic(
        verification: ReplayVerification,
    ) -> None:
        """Fail closed when replay fingerprints differ."""

        if not verification.deterministic:
            raise ReplayError(
                "Scenario replay fingerprint mismatch: "
                f"{verification.first.fingerprint} != "
                f"{verification.second.fingerprint}"
            )

    @staticmethod
    def _canonical_payload(
        result: ScenarioRunResult,
    ) -> dict[str, object]:
        return {
            "scenario_id": result.scenario_id,
            "validation_report": asdict(result.validation_report),
            "volunteer_results": [
                asdict(item)
                for item in result.volunteer_results
            ],
            "resource_results": [
                asdict(item)
                for item in result.resource_results
            ],
            "dispatch_decision": asdict(result.dispatch_decision),
            "reconstruction_report": asdict(
                result.reconstruction_report
            ),
        }