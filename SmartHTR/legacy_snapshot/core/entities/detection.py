"""
---------------------------------------------------------
Module    : detection.py
Project   : SmartHTR

Description:
    Represents one detected text region.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bounding_box import BoundingBox
from .metadata import Metadata


@dataclass(slots=True)
class Detection:
    """
    One text detection produced by the detector.
    """

    id: int

    page_number: int

    bbox: BoundingBox

    confidence: float

    metadata: Metadata = field(
        default_factory=Metadata
    )