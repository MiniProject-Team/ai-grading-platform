from __future__ import annotations

from dataclasses import dataclass, field

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class ScoreContribution:
    score: float
    weight: float
    contribution: float


@dataclass(frozen=True, slots=True)
class MarksResult:
    question_id: QuestionId
    max_marks: int | None
    marks_awarded: float | None
    percentage: float | None
    evaluation_status: str
    breakdown: dict[str, ScoreContribution] = field(default_factory=dict)
    note: str | None = None
