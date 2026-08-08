from __future__ import annotations

import logging

from domain.entities.model_answer import ModelAnswer

from .section_parser import NumberedSectionParser


class ModelAnswerParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str) -> list[ModelAnswer]:
        answers = self.section_parser.parse(text)
        if not answers:
            raise ValueError("No numbered model answers found")
        result = [ModelAnswer(section.question_id, section.text) for section in answers]
        self._validate_unique(result)
        self.logger.info("Model answers detected: %s", len(result))
        return result

    @staticmethod
    def _validate_unique(answers: list[ModelAnswer]) -> None:
        if len({answer.question_id for answer in answers}) != len(answers):
            raise ValueError("Duplicate question IDs in model answers")
