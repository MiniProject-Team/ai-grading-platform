"""Input boundary for the three independent SmartEval sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .loaders import ModelAnswerLoader, QuestionPaperLoader
from .student_text_provider import SmartHTRLocalOutputProvider, StudentTextProvider


@dataclass(frozen=True, slots=True)
class RawInputs:
    question_paper_text: str
    model_answer_text: str
    student_text: str


class InputManager:
    def __init__(
        self,
        question_loader: QuestionPaperLoader | None = None,
        model_loader: ModelAnswerLoader | None = None,
        student_provider: StudentTextProvider | None = None,
    ) -> None:
        self.question_loader = question_loader or QuestionPaperLoader()
        self.model_loader = model_loader or ModelAnswerLoader()
        self.student_provider = student_provider or SmartHTRLocalOutputProvider()
        self.logger = logging.getLogger("smarteval")

    def load(self, question_paper: Path, model_answer: Path, student_text: Path) -> RawInputs:
        question_text, model_text = self.load_teacher_inputs(question_paper, model_answer)
        student_text_value = self.load_student_text(student_text)
        return RawInputs(question_text, model_text, student_text_value)

    def load_teacher_inputs(self, question_paper: Path, model_answer: Path) -> tuple[str, str]:
        self.logger.info("Loading question paper: %s", question_paper)
        self.logger.info("Loading model answer: %s", model_answer)
        question_text = self.question_loader.load(question_paper)
        model_text = self.model_loader.load(model_answer)
        if not question_text.strip() or not model_text.strip():
            raise ValueError("Question paper and model answer must both be non-empty")
        return question_text, model_text

    def load_student_text(self, student_text: Path) -> str:
        self.logger.info("Loading student OCR text: %s", student_text)
        text = self.student_provider.get_text(student_text)
        if not text.strip():
            raise ValueError("Student text must be non-empty")
        return text
