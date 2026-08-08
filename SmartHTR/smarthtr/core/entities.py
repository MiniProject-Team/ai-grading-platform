"""Typed objects exchanged by every SmartHTR pipeline stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass(frozen=True, slots=True)
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True, slots=True)
class Detection:
    bbox: BoundingBox
    confidence: float
    page_number: int


@dataclass(slots=True)
class OCRResult:
    text: str = ""
    confidence: float | None = None
    model_name: str | None = None


@dataclass(slots=True)
class Line:
    id: int
    page_number: int
    bbox: BoundingBox
    image: np.ndarray
    processed_image: np.ndarray | None = None
    result: OCRResult = field(default_factory=OCRResult)


@dataclass(slots=True)
class Page:
    number: int
    original_image: np.ndarray
    processed_image: np.ndarray | None = None
    detections: list[Detection] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)

    @property
    def image(self) -> np.ndarray:
        return self.processed_image if self.processed_image is not None else self.original_image

    @property
    def text(self) -> str:
        return "\n".join(line.result.text for line in self.lines if line.result.text)


@dataclass(slots=True)
class Document:
    path: Path
    pages: list[Page] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text)
