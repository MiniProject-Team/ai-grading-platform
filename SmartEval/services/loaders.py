from __future__ import annotations

from pathlib import Path

from .text_extractor import TextExtractor


class QuestionPaperLoader:
    def __init__(self, extractor: TextExtractor | None = None) -> None: self.extractor = extractor or TextExtractor()
    def load(self, source: Path) -> str: return self.extractor.extract(source)


class ModelAnswerLoader:
    def __init__(self, extractor: TextExtractor | None = None) -> None: self.extractor = extractor or TextExtractor()
    def load(self, source: Path) -> str: return self.extractor.extract(source)
