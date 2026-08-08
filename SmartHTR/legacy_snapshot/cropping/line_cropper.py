"""Crop ordered page detections into line entities."""

from __future__ import annotations

from core.entities import Line, Page

from .base_cropper import BaseCropper


class LineCropper(BaseCropper):
    """Crop valid detected text regions from a page."""

    def __init__(self, padding: int = 5) -> None:
        self.padding = padding

    def crop(self, page: Page) -> None:
        page.lines.clear()
        image = page.image
        height, width = image.shape[:2]

        for detection in page.detections:
            bbox = detection.bbox
            x1 = max(0, int(bbox.left * width) - self.padding)
            y1 = max(0, int(bbox.top * height) - self.padding)
            x2 = min(width, int(bbox.right * width) + self.padding)
            y2 = min(height, int(bbox.bottom * height) + self.padding)

            if x2 <= x1 or y2 <= y1:
                continue

            page.lines.append(
                Line(
                    id=len(page.lines) + 1,
                    page_number=page.page_number,
                    bbox=bbox,
                    image=image[y1:y2, x1:x2].copy(),
                )
            )

        page.metadata.add(
            "cropping",
            {"padding": self.padding, "total_lines": len(page.lines)},
        )
