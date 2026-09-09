from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExamMetadata:
    institution: str | None = None
    exam_name: str | None = None
    academic_year: str | None = None
    semester: str | None = None
    branch: str | None = None
    subject: str | None = None
    subject_code: str | None = None
    date: str | None = None
    time: str | None = None
    max_marks: int | None = None
    instructions: list[str] = field(default_factory=list)


@dataclass
class ParsedQuestion:
    question_number: str
    sub_question: str | None
    question_text: str
    marks: int | None = None
    co: str | None = None
    question_type: str = "descriptive"
    alternative_group: str | None = None
    ocr_uncertain: bool = False


@dataclass
class Section:
    section_name: str | None
    questions: list[ParsedQuestion] = field(default_factory=list)


@dataclass
class ParsedPaper:
    document_type: str
    exam: ExamMetadata
    sections: list[Section]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
