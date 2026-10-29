"""An interval and its comparison rules.

Intervals are half-open: ``[start, end)``. Two intervals overlap when they
share at least one point, so touching endpoints (``[1, 3)`` and ``[3, 5)``)
do *not* overlap. This matches how time ranges, bookings, and genome
coordinates are usually modelled, and it keeps overlap tests free of
off-by-one ambiguity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, order=True)
class Interval:
    """A half-open interval ``[start, end)`` carrying an optional payload.

    ``payload`` is excluded from ordering so intervals sort by their
    endpoints, which is what the tree relies on. Payloads must be
    hashable because intervals are hashable.
    """

    start: float
    end: float
    payload: Any = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"empty or inverted interval: start={self.start!r} must be < end={self.end!r}"
            )

    def overlaps(self, other: "Interval") -> bool:
        """True when this interval shares at least one point with ``other``."""
        return self.start < other.end and other.start < self.end

    def contains_point(self, point: float) -> bool:
        """True when ``point`` lies inside ``[start, end)``."""
        return self.start <= point < self.end

    def __repr__(self) -> str:  # keep output compact in the CLI and REPL
        if self.payload is None:
            return f"Interval({self.start}, {self.end})"
        return f"Interval({self.start}, {self.end}, {self.payload!r})"
