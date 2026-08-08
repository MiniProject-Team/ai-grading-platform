"""DocTR detector implementation. It never performs final recognition."""

from __future__ import annotations

import logging

import numpy as np
from doctr.models import detection_predictor

from smarthtr.core.entities import BoundingBox, Detection
from smarthtr.core.exceptions import DetectionError
from smarthtr.core.interfaces import Detector


class DocTRDetector(Detector):
    def __init__(self, architecture: str = "db_resnet50") -> None:
        self.logger = logging.getLogger("smarthtr")
        try:
            self.model = detection_predictor(arch=architecture, pretrained=True)
        except Exception as error:
            raise DetectionError(f"Unable to load DocTR detector: {error}") from error

    def detect(self, image: np.ndarray, page_number: int) -> list[Detection]:
        try:
            prediction = self.model([image])[0]["words"]
        except Exception as error:
            raise DetectionError(f"DocTR detection failed on page {page_number}: {error}") from error
        detections = self.parse_predictions(prediction, page_number)
        self.logger.info("Page %s: detected %s text regions", page_number, len(detections))
        return detections

    @staticmethod
    def parse_predictions(prediction: np.ndarray, page_number: int) -> list[Detection]:
        words = [
            Detection(
                bbox=BoundingBox(float(left), float(top), float(right), float(bottom)),
                confidence=float(confidence),
                page_number=page_number,
            )
            for left, top, right, bottom, confidence in prediction
        ]
        return DocTRDetector.group_words_into_lines(words)

    @staticmethod
    def group_words_into_lines(words: list[Detection]) -> list[Detection]:
        """Merge word-level DocTR boxes into line-level recognition regions."""
        groups: list[list[Detection]] = []
        for word in sorted(words, key=lambda item: (item.bbox.top, item.bbox.left)):
            center = (word.bbox.top + word.bbox.bottom) / 2
            best_group = None
            best_distance = float("inf")
            for group in groups:
                centers = [(item.bbox.top + item.bbox.bottom) / 2 for item in group]
                heights = [item.bbox.bottom - item.bbox.top for item in group]
                group_center = sum(centers) / len(centers)
                tolerance = max(0.008, (sum(heights) / len(heights) + word.bbox.bottom - word.bbox.top) * 0.35)
                distance = abs(center - group_center)
                if distance <= tolerance and distance < best_distance:
                    best_group, best_distance = group, distance
            if best_group is None:
                groups.append([word])
            else:
                best_group.append(word)

        lines = []
        for group in groups:
            left = min(item.bbox.left for item in group)
            top = min(item.bbox.top for item in group)
            right = max(item.bbox.right for item in group)
            bottom = max(item.bbox.bottom for item in group)
            confidence = sum(item.confidence for item in group) / len(group)
            lines.append(Detection(BoundingBox(left, top, right, bottom), confidence, group[0].page_number))
        return sorted(lines, key=lambda item: (item.bbox.top, item.bbox.left))
