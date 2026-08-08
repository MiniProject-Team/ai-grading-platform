"""
---------------------------------------------------------
Module    : border_removal.py
Project   : SmartHTR

Description:
    Removes dark scanner borders while preserving
    the original page dimensions.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2
import numpy as np

from core.entities import Page


class BorderRemovalProcessor:
    """
    Remove dark page borders.
    """

    def __init__(
        self,
        threshold: int = 15,
    ) -> None:

        self.threshold = threshold

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Replace dark borders with white pixels.
        """

        image = page.image

        if len(image.shape) == 3:

            gray = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2GRAY,
            )

        else:

            gray = image

        _, mask = cv2.threshold(
            gray,
            self.threshold,
            255,
            cv2.THRESH_BINARY,
        )

        cleaned = image.copy()

        cleaned[mask == 0] = 255

        page.processed_image = cleaned

        page.metadata.add(
            "border_removal",
            {
                "applied": True,
                "threshold": self.threshold,
            },
        )