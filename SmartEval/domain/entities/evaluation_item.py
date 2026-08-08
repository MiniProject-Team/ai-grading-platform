from __future__ import annotations

from dataclasses import dataclass

from .model_answer import ModelAnswer
from .question import Question
from .student_answer import StudentAnswer


@dataclass(frozen=True, slots=True)
class EvaluationItem:
    question: Question
    model_answer: ModelAnswer | None
    student_answer: StudentAnswer

    @property
    def model_answer_missing(self) -> bool:
        return self.model_answer is None or not self.model_answer.answer_text.strip()

    @property
    def student_answer_missing(self) -> bool:
        return not self.student_answer.answer_text.strip()
