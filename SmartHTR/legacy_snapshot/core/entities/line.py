"""
---------------------------------------------------------
Module    : line.py
Project   : SmartHTR

Description:
    Represents one cropped text line.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .bounding_box import BoundingBox
from .metadata import Metadata
from .recognition import Recognition


@dataclass(slots=True)
class Line:
    """
    One cropped text line flowing through the OCR pipeline.
    """

    id: int

    page_number: int

    bbox: BoundingBox

    image: np.ndarray

    processed_image: np.ndarray | None = None

    recognition: Recognition = field(
        default_factory=Recognition
    )

    metadata: Metadata = field(
        default_factory=Metadata
    )