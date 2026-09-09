"""Heuristic, layout-independent parser for extracted question-paper text.

It deliberately treats absent data as unknown; it never manufactures marks or
metadata. OCR/layout engines can supply improved text to this same parser.
"""
from __future__ import annotations

import re

from .models import ExamMetadata, ParsedPaper, ParsedQuestion, Section

SECTION = re.compile(r"^\s*((?:section|part)\s*[a-z0-9ivx]+)\s*[:.-]?\s*$", re.I)
OR = re.compile(r"^\s*(?:or|either|alternatively|internal\s+choice)\s*$", re.I)
QUESTION = re.compile(r"^\s*(?:q(?:uestion)?\s*\.?\s*)?(\d{1,3})\s*(?:[.):-]\s*)?(.*)$", re.I)
SUBQUESTION = re.compile(r"^\s*(?:\(?([a-z]|[ivxlcdm]+)\)?[.)]|\(?([a-z]|[ivxlcdm]+)\))\s*(.*)$", re.I)
MARKS = re.compile(r"(?:\[|\()\s*(\d{1,2})\s*(?:marks?)?\s*(?:\]|\))|(?:marks?|m)\s*[:=-]?\s*(\d{1,2})\b|\b(\d{1,2})\s*marks?\b", re.I)
CO = re.compile(r"\b(?:co|course\s*outcome)\s*[:.-]?\s*([a-z0-9.-]+)\b", re.I)


class StructureParser:
    def parse(self, text: str, document_type: str = "text") -> ParsedPaper:
        lines = [self._clean(line) for line in text.splitlines()]
        metadata = self._metadata(lines)
        sections: list[Section] = []
        current = Section(None)
        sections.append(current)
        pending_or = False
        group_index = 0
        open_alternative_number: str | None = None
        active: ParsedQuestion | None = None
        last_number = ""

        for line in lines:
            if not line:
                continue
            section = SECTION.match(line)
            if section:
                current = Section(section.group(1).strip())
                sections.append(current); active = None
                continue
            if OR.match(line):
                pending_or = True; active = None
                continue
            parsed = self._question_from_line(line)
            if parsed:
                if not parsed.question_number:
                    parsed.question_number = last_number
                else:
                    last_number = parsed.question_number
                if pending_or:
                    group_index += 1
                    parsed.alternative_group = f"OR_{group_index}"
                    # Put the immediately preceding logical block in the same group.
                    for earlier in reversed(current.questions):
                        if earlier.question_number == (current.questions[-1].question_number if current.questions else ""):
                            earlier.alternative_group = parsed.alternative_group
                        else:
                            break
                    open_alternative_number = parsed.question_number
                    pending_or = False
                elif open_alternative_number == parsed.question_number:
                    parsed.alternative_group = f"OR_{group_index}"
                elif open_alternative_number:
                    open_alternative_number = None
                current.questions.append(parsed); active = parsed
            elif active and not self._looks_like_header(line):
                active.question_text = f"{active.question_text} {line}".strip()

        sections = [section for section in sections if section.questions]
        warnings = self._validate(metadata, sections)
        if not sections:
            warnings.append("No numbered questions were detected; review OCR text and structure manually.")
        return ParsedPaper(document_type, metadata, sections, warnings)

    def _question_from_line(self, line: str) -> ParsedQuestion | None:
        number = QUESTION.match(line)
        if number and (line.lower().startswith(("q", "question")) or number.group(2).strip()):
            number_text, remainder = number.group(1), number.group(2).strip()
            sub = SUBQUESTION.match(remainder)
            if sub:
                sub_id = (sub.group(1) or sub.group(2)).lower()
                remainder = sub.group(3).strip()
            else:
                sub_id = None
            return self._build(number_text, sub_id, remainder)
        sub = SUBQUESTION.match(line)
        if sub:
            return self._build("", (sub.group(1) or sub.group(2)).lower(), sub.group(3).strip())
        return None

    def _build(self, number: str, sub: str | None, value: str) -> ParsedQuestion:
        marks_match = MARKS.search(value)
        marks = int(next(item for item in marks_match.groups() if item is not None)) if marks_match else None
        co_match = CO.search(value)
        cleaned = MARKS.sub("", value)
        cleaned = CO.sub("", cleaned).strip(" -|\t")
        return ParsedQuestion(number, sub, cleaned, marks, co_match.group(1) if co_match else None, self._classify(cleaned), "", "[OCR UNCERTAIN]" in value)

    @staticmethod
    def _classify(text: str) -> str:
        lowered = text.lower()
        if re.search(r"\b(mcq|choose|true\s*/?\s*false)\b", lowered): return "objective"
        if re.search(r"\b(program|code|implement)\b", lowered): return "programming"
        if re.search(r"\b(calculate|numerical|solve)\b", lowered): return "numerical"
        if re.search(r"\b(compare|differentiate)\b", lowered): return "comparison"
        if re.search(r"\b(case study)\b", lowered): return "case_study"
        return "descriptive"

    @staticmethod
    def _clean(line: str) -> str:
        return re.sub(r"\s+", " ", line.replace("Q .", "Q.")).strip()

    @staticmethod
    def _looks_like_header(line: str) -> bool:
        return any(token in line.lower() for token in ("maximum marks", "time:", "instructions"))

    def _metadata(self, lines: list[str]) -> ExamMetadata:
        joined = "\n".join(lines[:40])
        field = lambda pattern: (match.group(1).strip() if (match := re.search(pattern, joined, re.I)) else None)
        max_value = field(r"(?:maximum|max)\s*marks?\s*[:=-]?\s*(\d+)")
        instructions = [line for line in lines if re.match(r"^\s*\d+[.)]\s+", line) and "instruction" in joined.lower()]
        return ExamMetadata(
            institution=lines[0] if lines else None,
            exam_name=field(r"(?:examination|exam)\s*[:=-]?\s*([^\n]+)"),
            academic_year=field(r"(?:academic year|a\.y\.)\s*[:=-]?\s*([^\n]+)"),
            semester=field(r"(?:semester|sem)\s*[:=-]?\s*([^\n]+)"),
            subject=field(r"(?:subject|course)\s*(?:name)?\s*[:=-]\s*([^\n]+)"),
            subject_code=field(r"(?:subject|course)\s*code\s*[:=-]?\s*([a-z0-9-]+)"),
            date=field(r"\bdate\s*[:=-]?\s*([^\n]+)"), time=field(r"(?:time|duration)\s*[:=-]?\s*([^\n]+)"),
            max_marks=int(max_value) if max_value else None, instructions=instructions)

    @staticmethod
    def _validate(exam: ExamMetadata, sections: list[Section]) -> list[str]:
        marks = [question.marks for section in sections for question in section.questions if question.marks is not None]
        warnings: list[str] = []
        if exam.max_marks is not None and marks and sum(marks) != exam.max_marks:
            warnings.append(f"Extracted question marks total = {sum(marks)}; paper maximum marks = {exam.max_marks}.")
        return warnings
