from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class Question:
    question_id: QuestionId
    question_number: int
    question_text: str
    max_marks: int | None

    def __post_init__(self) -> None:
        if self.question_number < 1:
            raise ValueError("Question number must be positive")
        if not self.question_text.strip():
            raise ValueError(f"Question {self.question_id} has empty text")
        if self.max_marks is not None and self.max_marks <= 0:
            raise ValueError(f"Question {self.question_id} has invalid maximum marks")
