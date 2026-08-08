"""Natural top-to-bottom, left-to-right line reconstruction."""

from __future__ import annotations

from smarthtr.core.entities import Line


class ReadingOrderReconstructor:
    def order(self, lines: list[Line]) -> list[Line]:
        return sorted(lines, key=lambda line: (round(line.bbox.top, 3), line.bbox.left))
