from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class RoundingPolicy:
    def __init__(self, decimal_places: int) -> None:
        if decimal_places not in {0, 1, 2}:
            raise ValueError("MARKS_DECIMAL_PLACES must be 0, 1, or 2")
        self.decimal_places = decimal_places

    def round_marks(self, value: float) -> float:
        return self._round(value, self.decimal_places)

    def round_percentage(self, value: float) -> float:
        return self._round(value, 2)

    @staticmethod
    def _round(value: float, decimal_places: int) -> float:
        quantizer = Decimal("1") if decimal_places == 0 else Decimal("1." + "0" * decimal_places)
        return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))
