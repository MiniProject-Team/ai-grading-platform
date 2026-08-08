"""
---------------------------------------------------------
Module    : resize.py
Project   : SmartHTR

Description:
    Resize oversized page images while preserving
    aspect ratio.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2

from core.entities import Page
from config.settings import settings


class ResizeProcessor:
    """
    Resize oversized page images.
    """

    def __init__(
        self,
        max_width: int = 2480,
        max_height: int = 3508,
    ) -> None:

        self.max_width = max_width
        self.max_height = max_height

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Resize the page if it exceeds the maximum size.
        """

        image = (
            page.processed_image
            if page.processed_image is not None
            else page.original_image
        )

        height, width = image.shape[:2]

        if (
            width <= self.max_width
            and height <= self.max_height
        ):
            page.processed_image = image

            page.metadata.add(
                "resize",
                {
                    "applied": False,
                    "scale": 1.0,
                },
            )

            return

        scale = min(
            self.max_width / width,
            self.max_height / height,
        )

        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

        page.processed_image = resized

        page.metadata.add(
            "resize",
            {
                "applied": True,
                "scale": scale,
                "width": new_width,
                "height": new_height,
            },
        )