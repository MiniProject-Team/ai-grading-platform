"""Turn normalized DocTR detections into cropped line images."""

from __future__ import annotations

import cv2

from smarthtr.core.entities import Detection, Line


class LineCropper:
    def __init__(self, padding: int = 8) -> None:
        self.padding = padding

    def crop(self, image, detections: list[Detection]) -> list[Line]:
        height, width = image.shape[:2]
        lines: list[Line] = []
        for detection in detections:
            box = detection.bbox
            x1, y1 = max(0, int(box.left * width) - self.padding), max(0, int(box.top * height) - self.padding)
            x2, y2 = min(width, int(box.right * width) + self.padding), min(height, int(box.bottom * height) + self.padding)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = image[y1:y2, x1:x2].copy()
            if crop.size:
                lines.append(Line(id=len(lines) + 1, page_number=detection.page_number, bbox=box, image=crop))
        return lines
