from __future__ import annotations

from pathlib import Path

from services.text_extractor import TextExtractor
from .answer_generator import AnswerGenerator
from .structure_parser import StructureParser


class QuestionPaperService:
    def __init__(self, extractor: TextExtractor | None = None) -> None:
        self.extractor = extractor or TextExtractor()
        self.parser = StructureParser()
        self.answers = AnswerGenerator()

    def analyze(self, source: Path):
        document_type = "digital_pdf" if source.suffix.lower() == ".pdf" else "text"
        return self.parser.parse(self.extractor.extract(source), document_type)

    def model_answer_sheet(self, source: Path, depth: str = "exam_ready") -> tuple[dict, str]:
        paper = self.analyze(source)
        return paper.to_dict(), self.answers.generate(paper, depth)
