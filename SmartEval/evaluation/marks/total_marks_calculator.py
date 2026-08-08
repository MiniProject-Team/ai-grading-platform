from __future__ import annotations

from domain.entities.marks_result import MarksResult
from domain.entities.total_marks_result import TotalMarksResult

from .rounding import RoundingPolicy


class TotalMarksCalculator:
    def __init__(self, rounding: RoundingPolicy) -> None:
        self.rounding = rounding

    def calculate(self, results: list[MarksResult]) -> TotalMarksResult:
        exam_maximum = sum(result.max_marks or 0 for result in results)
        evaluated = [result for result in results if result.marks_awarded is not None and result.max_marks is not None]
        evaluated_maximum = sum(result.max_marks for result in evaluated)
        awarded = self.rounding.round_marks(sum(result.marks_awarded for result in evaluated))
        percentage = self.rounding.round_percentage(awarded / evaluated_maximum * 100) if evaluated_maximum else None
        unevaluated = tuple(result.question_id for result in results if result.marks_awarded is None)
        return TotalMarksResult(
            awarded_marks=awarded,
            evaluated_maximum_marks=evaluated_maximum,
            exam_maximum_marks=exam_maximum,
            percentage=percentage,
            evaluated_questions=len(evaluated),
            missing_model_answers=sum(result.evaluation_status == "model_answer_missing" for result in results),
            unanswered_questions=sum(result.evaluation_status == "no_answer" for result in results),
            unevaluated_questions=unevaluated,
        )
