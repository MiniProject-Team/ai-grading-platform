from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer


class FeedbackGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        question: Question | None,
        model_answer: ModelAnswer | None,
        student_answer: StudentAnswer | None,
        evaluation_result: EvaluationResult | None,
        marks_result: MarksResult | None,
    ) -> FeedbackResult:
        """Generate explainable feedback for one consistently mapped question."""
