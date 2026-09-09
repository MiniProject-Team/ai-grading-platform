"""Extensible numbered-section parsing shared by question and answer documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


# A bare number is a heading only when it has an explicit delimiter.  The old
# optional-prefix pattern accepted OCR/table cells such as "4 marks" as Q4.
HEADER_PATTERN = re.compile(
    r"^\s*(?:(?:q(?:uestion)?|answer)\s*\.?\s*(?P<prefixed>\d+)(?:\s*[.):])?|(?P<bare>\d+)\s*[.):])(?:\s*(?P<body>.*))?\s*$",
    re.IGNORECASE,
)


def normalize_question_id(value: str) -> str:
    """Return a deterministic canonical ID for supported question labels."""
    match = re.match(r"^\s*(?:q(?:uestion)?\s*\.?)?\s*(\d+)\s*(?:\(?\s*([a-z]|[ivxlcdm]+)\s*\)?)?\s*[.):]?\s*$", value, re.I)
    if not match:
        raise ValueError(f"Unsupported question identifier: {value!r}")
    number, child = match.groups()
    return f"Q{int(number)}" + (f"({child.lower()})" if child else "")


@dataclass(frozen=True, slots=True)
class NumberedSection:
    question_id: QuestionId
    text: str


class NumberedSectionParser:
    def parse(self, text: str) -> list[NumberedSection]:
        sections: list[NumberedSection] = []
        current_number: int | None = None
        current_lines: list[str] = []
        for line in text.splitlines():
            match = HEADER_PATTERN.match(line)
            if match:
                if current_number is not None:
                    sections.append(NumberedSection(QuestionId(current_number), self._join(current_lines)))
                current_number = int(match.group("prefixed") or match.group("bare"))
                current_lines = [match.group("body") or ""]
            elif current_number is not None:
                current_lines.append(line)
        if current_number is not None:
            sections.append(NumberedSection(QuestionId(current_number), self._join(current_lines)))
        return sections

    @staticmethod
    def _join(lines: list[str]) -> str:
        return "\n".join(line.strip() for line in lines).strip()
