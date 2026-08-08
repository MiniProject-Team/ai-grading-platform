from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class ModelAnswer:
    question_id: QuestionId
    answer_text: str
