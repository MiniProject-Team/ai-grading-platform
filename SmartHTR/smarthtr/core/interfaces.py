"""Stable interfaces that make model replacement possible."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from .entities import Detection, Line, OCRResult


class Recognizer(ABC):
    @abstractmethod
    def load_model(self) -> None: ...

    @abstractmethod
    def recognize(self, line: Line) -> OCRResult: ...

    @abstractmethod
    def recognize_batch(self, lines: list[Line]) -> list[OCRResult]: ...


class Detector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray, page_number: int) -> list[Detection]: ...
