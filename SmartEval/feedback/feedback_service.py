from __future__ import annotations

import logging

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.value_objects.question_id import QuestionId

from .feedback_generator import FeedbackGenerator


class FeedbackService:
    def __init__(self, generator: FeedbackGenerator) -> None:
        self.generator = generator
        self.logger = logging.getLogger("smarteval")

    def generate(
        self,
        items: list[EvaluationItem],
        evaluations: list[EvaluationResult],
        marks_results: list[MarksResult],
    ) -> list[FeedbackResult]:
        evaluation_by_id = self._index(evaluations, "EvaluationResult")
        marks_by_id = self._index(marks_results, "MarksResult")
        item_ids = {item.question.question_id for item in items}
        if set(evaluation_by_id) != item_ids or set(marks_by_id) != item_ids:
            raise ValueError("Feedback generation requires one evaluation and one marks result for every mapped question")

        feedback: list[FeedbackResult] = []
        for item in items:
            question_id = item.question.question_id
            evaluation = evaluation_by_id[question_id]
            marks = marks_by_id[question_id]
            try:
                result = self.generator.generate(item.question, item.model_answer, item.student_answer, evaluation, marks)
            except Exception:
                self.logger.exception("Feedback generation failed for %s", question_id)
                raise
            self.logger.info(
                "Feedback generated for %s: marks=%s status=%s",
                question_id,
                marks.marks_awarded,
                evaluation.status,
            )
            feedback.append(result)
        return feedback

    @staticmethod
    def _index(results: list[EvaluationResult] | list[MarksResult], name: str) -> dict[QuestionId, EvaluationResult | MarksResult]:
        indexed = {result.question_id: result for result in results}
        if len(indexed) != len(results):
            raise ValueError(f"Duplicate question IDs in {name} list")
        return indexed
