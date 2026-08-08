from __future__ import annotations

from dataclasses import dataclass, field

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class TotalMarksResult:
    awarded_marks: float
    evaluated_maximum_marks: int
    exam_maximum_marks: int
    percentage: float | None
    evaluated_questions: int
    missing_model_answers: int
    unanswered_questions: int
    unevaluated_questions: tuple[QuestionId, ...] = field(default_factory=tuple)
