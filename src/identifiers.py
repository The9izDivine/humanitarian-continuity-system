"""Deterministic synthetic identifier generation."""

from __future__ import annotations

from dataclasses import dataclass, field


PREFIXES: dict[str, str] = {
    "incident": "INC",
    "household": "HH",
    "need": "NEED",
    "volunteer": "VOL",
    "resource": "RES",
    "plan": "PLAN",
    "decision": "DEC",
    "delivery": "DEL",
    "recovery": "RC",
    "evidence": "EV",
}


class IdentifierError(ValueError):
    """Raised when identifier generation receives invalid input."""


@dataclass
class IdentifierGenerator:
    """Generate deterministic, zero-padded identifiers by object type."""

    width: int = 6
    counters: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.width < 1:
            raise IdentifierError("Identifier width must be at least 1.")

        for object_type in PREFIXES:
            self.counters.setdefault(object_type, 0)

    def next(self, object_type: str) -> str:
        """Return the next identifier for a canonical object type."""

        if object_type not in PREFIXES:
            raise IdentifierError(f"Unsupported object type: {object_type}")

        self.counters[object_type] += 1
        prefix = PREFIXES[object_type]
        sequence = self.counters[object_type]

        return f"{prefix}-{sequence:0{self.width}d}"

    def peek(self, object_type: str) -> str:
        """Return the next identifier without incrementing the counter."""

        if object_type not in PREFIXES:
            raise IdentifierError(f"Unsupported object type: {object_type}")

        prefix = PREFIXES[object_type]
        sequence = self.counters[object_type] + 1

        return f"{prefix}-{sequence:0{self.width}d}"

    def reset(self, object_type: str | None = None) -> None:
        """Reset one counter or all counters."""

        if object_type is None:
            for key in self.counters:
                self.counters[key] = 0
            return

        if object_type not in PREFIXES:
            raise IdentifierError(f"Unsupported object type: {object_type}")

        self.counters[object_type] = 0