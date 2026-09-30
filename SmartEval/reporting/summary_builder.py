from __future__ import annotations

from domain.entities.evaluation_report import EvaluationSummary
from domain.entities.total_marks_result import TotalMarksResult


class SummaryBuilder:
    """Adapt the authoritative Phase 6 total into the report summary."""

    def build(self, total_marks: TotalMarksResult, total_questions: int) -> EvaluationSummary:
        if total_questions < 1:
            raise ValueError("An evaluation report requires at least one question")
        return EvaluationSummary(
            total_questions=total_questions,
            evaluated_questions=total_marks.evaluated_questions,
            unanswered_questions=total_marks.unanswered_questions,
            missing_model_answers=total_marks.missing_model_answers,
            awarded_marks=total_marks.awarded_marks,
            evaluated_maximum_marks=total_marks.evaluated_maximum_marks,
            exam_maximum_marks=total_marks.exam_maximum_marks,
            percentage=total_marks.percentage,
            or_groups=total_marks.or_groups,
        )
