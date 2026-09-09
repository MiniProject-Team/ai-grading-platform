from __future__ import annotations

import logging

from domain.entities.model_answer import ModelAnswer
from domain.value_objects.question_id import QuestionId
from question_paper.canonical import QuestionHierarchyParser

from .section_parser import NumberedSectionParser


class ModelAnswerParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.hierarchy_parser = QuestionHierarchyParser(allow_bare_numbers=False)
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str) -> list[ModelAnswer]:
        # Model answers commonly contain numbered explanation steps. Only
        # explicit Q/Question headings define answer boundaries here.
        hierarchical = self.hierarchy_parser.parse(text)
        if hierarchical and any(item.subquestions for item in hierarchical):
            result = []
            for parent in hierarchical:
                pieces = [parent.text] if parent.text else []
                pieces.extend(f"({child.label}) {child.text}" for child in parent.subquestions)
                result.append(ModelAnswer(QuestionId(int(parent.number)), "\n".join(pieces).strip()))
            self._validate_unique(result)
            self.logger.info("Canonical model answers detected: %s", len(result))
            return result
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
