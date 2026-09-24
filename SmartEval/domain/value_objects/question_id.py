from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class QuestionId:
    number: int
    subpart: str | None = None

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Question ID must be positive")
        if self.subpart is not None:
            normalized_subpart = self.subpart.strip().lower()
            if not re.fullmatch(r"[a-z]", normalized_subpart):
                raise ValueError("Question ID subpart must contain lowercase letters only")
            object.__setattr__(self, "subpart", normalized_subpart)

    def __str__(self) -> str:
        return f"Q{self.number}" if self.subpart is None else f"Q{self.number}({self.subpart})"
