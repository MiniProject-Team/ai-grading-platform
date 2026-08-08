"""
---------------------------------------------------------
Module    : bounding_box.py
Project   : SmartHTR

Description:
    Bounding box representation shared across
    the OCR pipeline.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BoundingBox:
    """
    Axis-aligned bounding box using normalized coordinates.

    Coordinates are stored in the range [0.0, 1.0].
    """

    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[float, float]:
        return (
            (self.left + self.right) / 2,
            (self.top + self.bottom) / 2,
        )

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (
            self.left,
            self.top,
            self.right,
            self.bottom,
        )