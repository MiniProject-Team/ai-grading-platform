from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class StudentAnswer:
    question_id: QuestionId
    answer_text: str
    mapping_method: str = "explicit_heading"
    mapping_confidence: float = 1.0
    pages: tuple[int, ...] = ()
