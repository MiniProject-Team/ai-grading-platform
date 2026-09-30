from __future__ import annotations

from domain.entities.marks_result import MarksResult
from domain.entities.total_marks_result import TotalMarksResult

from .rounding import RoundingPolicy
from .effective_earned_marks import calculate_effective_earned_marks
from .effective_max_marks import MarkedQuestion, calculate_effective_max_marks


class TotalMarksCalculator:
    def __init__(self, rounding: RoundingPolicy) -> None:
        self.rounding = rounding

    def calculate(self, results: list[MarksResult], questions: list[MarkedQuestion] | None = None) -> TotalMarksResult:
        paper = questions if questions is not None else results
        exam_maximum = calculate_effective_max_marks(paper)
        evaluated = [result for result in results if result.marks_awarded is not None and result.max_marks is not None]
        evaluated_ids = {result.question_id for result in evaluated}
        evaluated_maximum = calculate_effective_max_marks(q for q in paper if q.question_id in evaluated_ids)
        aggregation = calculate_effective_earned_marks(results, paper)
        awarded = self.rounding.round_marks(aggregation.earned)
        percentage = self.rounding.round_percentage(aggregation.earned / exam_maximum * 100) if exam_maximum else None
        unevaluated = tuple(result.question_id for result in results if result.marks_awarded is None)
        return TotalMarksResult(
            awarded_marks=awarded,
            or_groups=aggregation.or_groups,
            evaluated_maximum_marks=evaluated_maximum,
            exam_maximum_marks=exam_maximum,
            percentage=percentage,
            evaluated_questions=len(evaluated),
            missing_model_answers=sum(result.evaluation_status == "model_answer_missing" for result in results),
            unanswered_questions=sum(result.evaluation_status == "no_answer" for result in results),
            unevaluated_questions=unevaluated,
        )
