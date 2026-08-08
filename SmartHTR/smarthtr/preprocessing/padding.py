"""Prepare cropped lines for TrOCR's image processor."""

from __future__ import annotations

import cv2

from smarthtr.core.entities import Line

from .enhancement import enhance


class LinePreprocessor:
    def __init__(self, target_height: int = 64, padding: int = 12) -> None:
        self.target_height = target_height
        self.padding = padding

    def process(self, line: Line) -> Line:
        image = enhance(line.image)
        height, width = image.shape[:2]
        resized = cv2.resize(image, (max(1, round(width * self.target_height / height)), self.target_height), interpolation=cv2.INTER_CUBIC)
        line.processed_image = cv2.copyMakeBorder(resized, self.padding, self.padding, self.padding, self.padding, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        return line
