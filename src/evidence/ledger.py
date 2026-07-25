"""Immutable in-memory evidence ledger."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class EvidenceError(ValueError):
    """Base evidence-ledger error."""


class DuplicateEvidenceError(EvidenceError):
    """Raised when an evidence identifier already exists."""


class EvidenceNotFoundError(EvidenceError):
    """Raised when evidence cannot be found."""


@dataclass(frozen=True)
class EvidenceRecord:
    """Canonical evidence record."""

    evidence_id: str
    object_id: str
    property_name: str
    observed_value: Any
    observed_at: str
    source: str
    verification_state: str
    confidence: float | None = None
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise EvidenceError("Evidence identifier is required.")

        if not self.object_id:
            raise EvidenceError("Object identifier is required.")

        if not self.property_name:
            raise EvidenceError("Property name is required.")

        if not self.source:
            raise EvidenceError("Evidence source is required.")

        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise EvidenceError("Confidence must be between 0 and 1.")

        try:
            datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceError(
                f"Invalid observed_at timestamp: {self.observed_at}"
            ) from exc


@dataclass
class EvidenceLedger:
    """Append-only evidence ledger with deterministic retrieval."""

    _records: dict[str, EvidenceRecord] = field(default_factory=dict)

    def append(self, record: EvidenceRecord) -> None:
        """Append a new evidence record."""

        if record.evidence_id in self._records:
            raise DuplicateEvidenceError(
                f"Evidence already exists: {record.evidence_id}"
            )

        self._records[record.evidence_id] = record

    def get(self, evidence_id: str) -> EvidenceRecord:
        """Return a defensive copy of an evidence record."""

        if evidence_id not in self._records:
            raise EvidenceNotFoundError(
                f"Evidence not found: {evidence_id}"
            )

        return deepcopy(self._records[evidence_id])

    def for_object(self, object_id: str) -> tuple[EvidenceRecord, ...]:
        """Return all evidence records for an object."""

        return tuple(
            deepcopy(record)
            for record in sorted(
                self._records.values(),
                key=lambda item: item.evidence_id,
            )
            if record.object_id == object_id
        )

    def current_for_property(
        self,
        object_id: str,
        property_name: str,
    ) -> EvidenceRecord | None:
        """Return the latest non-superseded record for one property."""

        candidates = [
            record
            for record in self._records.values()
            if record.object_id == object_id
            and record.property_name == property_name
            and record.superseded_by is None
        ]

        if not candidates:
            return None

        return deepcopy(
            max(
                candidates,
                key=lambda item: datetime.fromisoformat(
                    item.observed_at.replace("Z", "+00:00")
                ),
            )
        )

    def supersede(
        self,
        evidence_id: str,
        replacement_evidence_id: str,
    ) -> None:
        """Mark one record as superseded by another existing record."""

        if evidence_id not in self._records:
            raise EvidenceNotFoundError(
                f"Evidence not found: {evidence_id}"
            )

        if replacement_evidence_id not in self._records:
            raise EvidenceNotFoundError(
                f"Replacement evidence not found: {replacement_evidence_id}"
            )

        original = self._records[evidence_id]

        if original.superseded_by is not None:
            raise EvidenceError(
                f"Evidence already superseded: {evidence_id}"
            )

        self._records[evidence_id] = EvidenceRecord(
            evidence_id=original.evidence_id,
            object_id=original.object_id,
            property_name=original.property_name,
            observed_value=original.observed_value,
            observed_at=original.observed_at,
            source=original.source,
            verification_state=original.verification_state,
            confidence=original.confidence,
            superseded_by=replacement_evidence_id,
        )

    def count(self) -> int:
        """Return total evidence-record count."""

        return len(self._records)

    def snapshot(self) -> tuple[EvidenceRecord, ...]:
        """Return all records in deterministic identifier order."""

        return tuple(
            deepcopy(self._records[evidence_id])
            for evidence_id in sorted(self._records)
        )


def utc_now_iso() -> str:
    """Return a normalized UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")