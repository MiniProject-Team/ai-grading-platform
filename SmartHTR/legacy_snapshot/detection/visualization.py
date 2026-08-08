"""
---------------------------------------------------------
Module    : visualization.py
Project   : SmartHTR

Description:
    Visualization utilities for detected text regions.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2
import numpy as np

from core.entities import Page


class DetectionVisualizer:
    """
    Draw detection results on page images.
    """

    def draw(
        self,
        page: Page,
    ) -> np.ndarray:
        """
        Draw bounding boxes and IDs.
        """

        image = page.image.copy()

        if len(image.shape) == 2:
            image = cv2.cvtColor(
                image,
                cv2.COLOR_GRAY2RGB,
            )

        height, width = image.shape[:2]

        for detection in page.detections:

            bbox = detection.bbox

            x1 = int(bbox.left * width)
            y1 = int(bbox.top * height)

            x2 = int(bbox.right * width)
            y2 = int(bbox.bottom * height)

            cv2.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                image,
                str(detection.id),
                (x1, max(20, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )

        return image