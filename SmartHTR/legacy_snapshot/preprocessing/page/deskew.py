"""
---------------------------------------------------------
Module    : deskew.py
Project   : SmartHTR

Description:
    Correct page skew using the minimum area rectangle.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2
import numpy as np

from core.entities import Page


class DeskewProcessor:
    """
    Correct page rotation.
    """

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Deskew the current page image.
        """

        image = page.image

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY,
        )

        _, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )

        coordinates = np.column_stack(
            np.where(binary > 0)
        )

        if len(coordinates) == 0:

            page.processed_image = image

            page.metadata.add(
                "deskew",
                {
                    "applied": False,
                    "angle": 0.0,
                },
            )

            return

        angle = cv2.minAreaRect(
            coordinates
        )[-1]

        if angle < -45:
            angle = 90 + angle

        center = (
            image.shape[1] // 2,
            image.shape[0] // 2,
        )

        matrix = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0,
        )

        rotated = cv2.warpAffine(
            image,
            matrix,
            (
                image.shape[1],
                image.shape[0],
            ),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        page.processed_image = rotated

        page.metadata.add(
            "deskew",
            {
                "applied": True,
                "angle": angle,
            },
        )