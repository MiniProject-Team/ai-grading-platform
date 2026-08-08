from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionId:
    number: int

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Question ID must be positive")

    def __str__(self) -> str:
        return f"Q{self.number}"
