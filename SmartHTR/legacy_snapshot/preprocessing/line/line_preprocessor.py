"""
---------------------------------------------------------
Module    : line_preprocessor.py
Project   : SmartHTR

Description:
    Prepare cropped lines for TrOCR recognition.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2

from core.entities import Line

from .utils import trim_white_border


class LinePreprocessor:
    """
    Prepare cropped lines for OCR.
    """

    def __init__(
        self,
        target_height: int = 64,
        padding: int = 10,
    ) -> None:

        self.target_height = target_height
        self.padding = padding

    def process(
        self,
        line: Line,
    ) -> None:
        """
        Process one cropped line.
        """

        image = trim_white_border(
            line.image
        )

        image = cv2.copyMakeBorder(
            image,
            self.padding,
            self.padding,
            self.padding,
            self.padding,
            cv2.BORDER_CONSTANT,
            value=255,
        )

        height, width = image.shape[:2]

        scale = self.target_height / height

        new_width = int(width * scale)

        resized = cv2.resize(
            image,
            (new_width, self.target_height),
            interpolation=cv2.INTER_CUBIC,
        )

        line.processed_image = resized

        line.metadata.add(
            "line_preprocessing",
            {
                "target_height": self.target_height,
                "padding": self.padding,
            },
        )