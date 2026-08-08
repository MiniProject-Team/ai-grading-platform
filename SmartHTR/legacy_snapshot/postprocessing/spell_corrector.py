"""Extension point for line-level spell correction."""

from __future__ import annotations

from core.entities import Line


class SpellCorrector:
    """Leave recognized text unchanged until a dictionary is configured."""

    def process(self, line: Line) -> None:
        return None
