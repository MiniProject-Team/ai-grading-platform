from __future__ import annotations

import logging

from domain.entities.student_answer import StudentAnswer

from .section_parser import NumberedSectionParser


class StudentAnswerParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str) -> list[StudentAnswer]:
        sections = self.section_parser.parse(text)
        if not sections:
            raise ValueError("No numbered student answers found")
        answers = [StudentAnswer(section.question_id, section.text) for section in sections]
        if len({answer.question_id for answer in answers}) != len(answers):
            raise ValueError("Duplicate question IDs in student answers")
        self.logger.info("Student answers detected: %s", len(answers))
        return answers
