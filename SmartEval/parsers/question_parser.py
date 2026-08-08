"""Parse numbered teacher questions and optional maximum marks."""

from __future__ import annotations

import logging
import re

from domain.entities.question import Question
from domain.value_objects.question_id import QuestionId

from .section_parser import NumberedSectionParser


MARKS_PATTERN = re.compile(
    r"(?:\[\s*(?P<bracket>\d+)(?:\s*marks?)?\s*\]|\(\s*(?P<paren>\d+)(?:\s*marks?)?\s*\)|\b(?P<suffix>\d+)\s+marks?\b|\bmarks?\s*:\s*(?P<prefix>\d+)\b)",
    re.IGNORECASE,
)


class QuestionParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str) -> list[Question]:
        questions = []
        seen_ids: set[QuestionId] = set()
        for section in self.section_parser.parse(text):
            if section.question_id in seen_ids:
                raise ValueError(f"Duplicate question ID: {section.question_id}")
            question_text, max_marks = self._extract_marks(section.text)
            if not question_text:
                raise ValueError(f"Question {section.question_id} has empty text")
            if max_marks is None:
                self.logger.warning("Maximum marks unavailable for %s", section.question_id)
            questions.append(Question(section.question_id, section.question_id.number, question_text, max_marks))
            seen_ids.add(section.question_id)
        if not questions:
            raise ValueError("No numbered questions found in question paper")
        self.logger.info("Questions detected: %s", len(questions))
        return questions

    @staticmethod
    def _extract_marks(text: str) -> tuple[str, int | None]:
        match = MARKS_PATTERN.search(text)
        if match is None:
            return text.strip(), None
        marks = next(int(value) for value in match.groupdict().values() if value is not None)
        return MARKS_PATTERN.sub("", text, count=1).strip(), marks
