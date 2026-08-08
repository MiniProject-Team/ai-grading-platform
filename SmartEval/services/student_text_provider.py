from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .text_extractor import TextExtractor


class StudentTextProvider(ABC):
    @abstractmethod
    def get_text(self, source: Path) -> str: ...


class LocalFileStudentTextProvider(StudentTextProvider):
    def __init__(self, extractor: TextExtractor | None = None) -> None: self.extractor = extractor or TextExtractor()
    def get_text(self, source: Path) -> str: return self.extractor.extract(source)


class SmartHTRLocalOutputProvider(LocalFileStudentTextProvider):
    """Consumes SmartHTR's ordered UTF-8 page-text exports without importing SmartHTR code."""
