"""
---------------------------------------------------------
Module    : doctr_detector.py
Project   : SmartHTR

Description:
    Detect handwritten text regions using DocTR.
---------------------------------------------------------
"""

from __future__ import annotations

from doctr.models import detection_predictor

from core.entities import BoundingBox
from core.entities import Detection
from core.entities import Page

from .base_detector import BaseDetector


class DocTRDetector(BaseDetector):
    """
    Detect handwritten text regions using DocTR.
    """

    def __init__(
        self,
        architecture: str = "db_resnet50",
        pretrained: bool = True,
    ) -> None:

        self.model = detection_predictor(
            arch=architecture,
            pretrained=pretrained,
        )

    def _predict(
        self,
        image,
    ):
        """
        Execute DocTR detection.
        """

        return self.model([image])

    def _parse_predictions(
        self,
        page: Page,
        result,
    ) -> None:
        """
        Convert DocTR predictions into Detection entities.
        """

        page.detections.clear()

        predictions = result[0]["words"]

        for detection_id, prediction in enumerate(predictions, start=1):
            left, top, right, bottom, confidence = prediction
            page.detections.append(
                Detection(
                    id=detection_id,
                    page_number=page.page_number,
                    bbox=BoundingBox(
                        left=float(left),
                        top=float(top),
                        right=float(right),
                        bottom=float(bottom),
                    ),
                    confidence=float(confidence),
                )
            )

    def detect(
        self,
        page: Page,
    ) -> None:
        """
        Detect text regions.
        """

        result = self._predict(
            page.image
        )

        self._parse_predictions(
            page,
            result,
        )

        page.metadata.add(
            "detection",
            {
                "model": "DocTR",
                "total_regions": len(
                    page.detections
                ),
            },
        )
