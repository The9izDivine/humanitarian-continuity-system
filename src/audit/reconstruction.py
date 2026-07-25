"""Decision reconstruction engine."""

from __future__ import annotations

from src.audit.models import (
    ReconstructionCondition,
    ReconstructionReport,
)
from src.dispatch.models import DispatchDecision
from src.evidence import EvidenceLedger


class ReconstructionError(ValueError):
    """Raised when a decision cannot be reconstructed safely."""


class DecisionReconstructionEngine:
    """Reconstruct a dispatch decision from policy results and evidence."""

    def reconstruct(
        self,
        *,
        decision: DispatchDecision,
        ledger: EvidenceLedger,
    ) -> ReconstructionReport:
        """Build a deterministic human-readable reconstruction."""

        conditions = tuple(
            ReconstructionCondition(
                condition_id=condition.condition_id,
                status=self._status(condition.satisfied),
                evidence_ids=condition.evidence_ids,
                explanation=condition.explanation,
            )
            for condition in decision.conditions
        )

        missing_evidence = tuple(
            evidence_id
            for evidence_id in decision.evidence_ids
            if not self._ledger_contains(ledger, evidence_id)
        )

        if missing_evidence:
            raise ReconstructionError(
                "Decision references missing evidence: "
                + ", ".join(missing_evidence)
            )

        timeline = self._build_timeline(
            decision=decision,
            ledger=ledger,
        )

        summary = self._build_summary(decision)

        return ReconstructionReport(
            decision_id=decision.decision_id,
            response_plan_id=decision.response_plan_id,
            incident_id=decision.incident_id,
            decision=decision.decision,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            decided_at=decision.decided_at,
            valid_until=decision.valid_until,
            failed_conditions=decision.failed_conditions,
            unknown_conditions=decision.unknown_conditions,
            evidence_ids=decision.evidence_ids,
            conditions=conditions,
            summary=summary,
            timeline=timeline,
        )

    @staticmethod
    def to_text(report: ReconstructionReport) -> str:
        """Render a reconstruction report as deterministic text."""

        lines = [
            "DECISION RECONSTRUCTION",
            "=======================",
            f"Decision ID      : {report.decision_id}",
            f"Response Plan    : {report.response_plan_id}",
            f"Incident         : {report.incident_id}",
            f"Decision         : {report.decision}",
            f"Policy           : {report.policy_id} {report.policy_version}",
            f"Decided At       : {report.decided_at}",
            f"Valid Until      : {report.valid_until or '<none>'}",
            f"Failed Conditions: {', '.join(report.failed_conditions) or '<none>'}",
            f"Unknown Conditions: {', '.join(report.unknown_conditions) or '<none>'}",
            "",
            "Condition Results",
            "-----------------",
        ]

        for condition in report.conditions:
            lines.append(
                f"{condition.condition_id}: {condition.status}"
            )
            lines.append(
                f"  Evidence: {', '.join(condition.evidence_ids) or '<none>'}"
            )
            lines.append(
                f"  Explanation: {condition.explanation}"
            )

        lines.extend(
            [
                "",
                "Timeline",
                "--------",
                *report.timeline,
                "",
                "Summary",
                "-------",
                report.summary,
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _status(value: bool | None) -> str:
        if value is True:
            return "SATISFIED"

        if value is False:
            return "FAILED"

        return "UNKNOWN"

    @staticmethod
    def _ledger_contains(
        ledger: EvidenceLedger,
        evidence_id: str,
    ) -> bool:
        try:
            ledger.get(evidence_id)
        except Exception:
            return False

        return True

    @staticmethod
    def _build_timeline(
        *,
        decision: DispatchDecision,
        ledger: EvidenceLedger,
    ) -> tuple[str, ...]:
        entries: list[tuple[str, str]] = []

        for evidence_id in decision.evidence_ids:
            record = ledger.get(evidence_id)

            entries.append(
                (
                    record.observed_at,
                    (
                        f"{record.observed_at} | {record.evidence_id} | "
                        f"{record.object_id}.{record.property_name} = "
                        f"{record.observed_value!r} | "
                        f"{record.verification_state}"
                    ),
                )
            )

        entries.append(
            (
                decision.decided_at,
                (
                    f"{decision.decided_at} | {decision.decision_id} | "
                    f"DECISION = {decision.decision}"
                ),
            )
        )

        return tuple(
            text
            for _, text in sorted(entries, key=lambda item: item[0])
        )

    @staticmethod
    def _build_summary(
        decision: DispatchDecision,
    ) -> str:
        if decision.failed_conditions:
            return (
                f"Response plan {decision.response_plan_id} produced "
                f"{decision.decision} because these mandatory conditions "
                f"failed: {', '.join(decision.failed_conditions)}."
            )

        if decision.unknown_conditions:
            return (
                f"Response plan {decision.response_plan_id} produced "
                f"{decision.decision} because these mandatory conditions "
                f"were unknown: {', '.join(decision.unknown_conditions)}."
            )

        return (
            f"Response plan {decision.response_plan_id} produced "
            f"{decision.decision} because every mandatory dispatch "
            "condition was satisfied."
        )