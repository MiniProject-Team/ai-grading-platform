from __future__ import annotations

from abc import ABC, abstractmethod
import logging

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.marks_result import MarksResult
from domain.entities.question import Question

from .rounding import RoundingPolicy
from .scoring_config import ScoringStrategy


class MarksCalculator(ABC):
    @abstractmethod
    def calculate(self, question: Question, evaluation: EvaluationResult) -> MarksResult: ...


class WeightedMarksCalculator(MarksCalculator):
    def __init__(self, strategy: ScoringStrategy, rounding: RoundingPolicy) -> None:
        self.strategy = strategy
        self.rounding = rounding
        self.logger = logging.getLogger("smarteval")

    def calculate(self, question: Question, evaluation: EvaluationResult) -> MarksResult:
        if question.question_id != evaluation.question_id:
            raise ValueError("Question and evaluation result IDs must match")
        if question.max_marks is None:
            return MarksResult(question.question_id, None, None, None, "max_marks_unavailable", note="Maximum marks unavailable; marks were not calculated.")
        if question.max_marks <= 0:
            raise ValueError("Question maximum marks must be positive")
        if evaluation.status == "model_answer_missing":
            self.logger.warning("Marks not awarded for %s because model answer is missing", question.question_id)
            return MarksResult(question.question_id, question.max_marks, None, None, evaluation.status, note="Model answer missing; evaluation is incomplete.")
        if evaluation.status == "no_answer":
            return MarksResult(question.question_id, question.max_marks, 0.0, 0.0, evaluation.status, note="No student answer was detected.")

        score, breakdown = self.strategy.calculate_score(evaluation)
        bounded_marks = min(question.max_marks, max(0.0, score * question.max_marks))
        awarded = min(float(question.max_marks), max(0.0, self.rounding.round_marks(bounded_marks)))
        percentage = self.rounding.round_percentage(awarded / question.max_marks * 100)
        self.logger.info("Marks calculated for %s: %.2f/%s", question.question_id, awarded, question.max_marks)
        return MarksResult(question.question_id, question.max_marks, awarded, percentage, evaluation.status, breakdown)
