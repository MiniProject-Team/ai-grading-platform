"""
---------------------------------------------------------
Module    : denoise.py
Project   : SmartHTR

Description:
    Removes image noise while preserving handwritten
    character edges.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2

from core.entities import Page


class DenoiseProcessor:
    """
    Reduce scanner noise using Non-Local Means denoising.
    """

    def __init__(
        self,
        h: int = 10,
        template_window_size: int = 7,
        search_window_size: int = 21,
    ) -> None:

        self.h = h
        self.template_window_size = template_window_size
        self.search_window_size = search_window_size

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Apply denoising to the current page image.
        """

        image = page.image

        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            self.h,
            self.h,
            self.template_window_size,
            self.search_window_size,
        )

        page.processed_image = denoised

        page.metadata.add(
            "denoise",
            {
                "applied": True,
                "method": "fastNlMeansDenoisingColored",
                "h": self.h,
            },
        )