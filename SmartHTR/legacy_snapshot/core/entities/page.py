"""
---------------------------------------------------------
Module    : page.py
Project   : SmartHTR

Description:
    Represents one page within a document.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .detection import Detection
from .line import Line
from .metadata import Metadata


@dataclass(slots=True)
class Page:
    """
    Represents one document page.
    """

    page_number: int

    original_image: np.ndarray

    processed_image: np.ndarray | None = None

    detections: list[Detection] = field(default_factory=list)

    lines: list[Line] = field(default_factory=list)

    metadata: Metadata = field(default_factory=Metadata)

    @property
    def image(self) -> np.ndarray:
        """
        Returns the current working image.

        If the page has already been processed, return the
        processed image; otherwise return the original image.
        """
        return (
            self.processed_image
            if self.processed_image is not None
            else self.original_image
        )