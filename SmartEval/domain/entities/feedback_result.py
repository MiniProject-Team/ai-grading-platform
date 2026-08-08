from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class FeedbackResult:
    """Concise, explainable feedback for one evaluated answer."""

    question_id: QuestionId
    marks_awarded: float | None
    max_marks: int | None
    status: str
    strengths: tuple[str, ...]
    missing_concepts: tuple[str, ...]
    weak_areas: tuple[str, ...]
    improvement_suggestions: tuple[str, ...]
    overall_feedback: str
