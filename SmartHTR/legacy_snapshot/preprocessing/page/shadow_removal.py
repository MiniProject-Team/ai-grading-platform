"""
---------------------------------------------------------
Module    : shadow_removal.py
Project   : SmartHTR

Description:
    Removes background shadows from scanned documents.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2
import numpy as np

from core.entities import Page


class ShadowRemovalProcessor:
    """
    Remove uneven page illumination.
    """

    def __init__(
        self,
        kernel_size: int = 25,
    ) -> None:

        self.kernel_size = kernel_size

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Remove page shadows.
        """

        image = page.image

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY,
        )

        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (self.kernel_size, self.kernel_size),
        )

        background = cv2.morphologyEx(
            gray,
            cv2.MORPH_CLOSE,
            kernel,
        )

        normalized = cv2.divide(
            gray,
            background,
            scale=255,
        )

        result = cv2.cvtColor(
            normalized,
            cv2.COLOR_GRAY2RGB,
        )

        page.processed_image = result

        page.metadata.add(
            "shadow_removal",
            {
                "applied": True,
                "kernel_size": self.kernel_size,
                "method": "Morphological Closing",
            },
        )