from __future__ import annotations

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_report import QuestionEvaluationResult
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.value_objects.question_id import QuestionId

from .exceptions import ReportValidationError


class ReportBuilder:
    """Combine existing Phase 4-7 results without recalculating them."""

    def build_question_results(
        self,
        items: list[EvaluationItem],
        evaluations: list[EvaluationResult],
        marks_results: list[MarksResult],
        feedback_results: list[FeedbackResult],
    ) -> list[QuestionEvaluationResult]:
        evaluations_by_id = self._index(evaluations, "EvaluationResult")
        marks_by_id = self._index(marks_results, "MarksResult")
        feedback_by_id = self._index(feedback_results, "FeedbackResult")
        item_ids = {item.question.question_id for item in items}
        if set(evaluations_by_id) != item_ids or set(marks_by_id) != item_ids or set(feedback_by_id) != item_ids:
            raise ReportValidationError("Report generation requires one evaluation, marks result, and feedback result per mapped question")
        return [
            QuestionEvaluationResult(
                question_id=item.question.question_id,
                question_text=item.question.question_text,
                max_marks=item.question.max_marks,
                student_answer=item.student_answer.answer_text,
                model_answer=item.model_answer.answer_text if item.model_answer else None,
                evaluation=evaluations_by_id[item.question.question_id],
                marks=marks_by_id[item.question.question_id],
                feedback=feedback_by_id[item.question.question_id],
            )
            for item in items
        ]

    @staticmethod
    def _index(results: list[object], name: str) -> dict[QuestionId, object]:
        indexed = {result.question_id: result for result in results}
        if len(indexed) != len(results):
            raise ReportValidationError(f"Duplicate question IDs in {name} list")
        return indexed
