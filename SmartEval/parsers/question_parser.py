"""Parse numbered teacher questions and optional maximum marks."""

from __future__ import annotations

import logging
import re

from domain.entities.question import Question
from domain.value_objects.question_id import QuestionId
from question_paper.canonical import QuestionHierarchyParser

from .section_parser import NumberedSectionParser


MARKS_PATTERN = re.compile(
    r"(?:\[\s*(?P<bracket>\d+)(?:\s*marks?)?\s*\]|\(\s*(?P<paren>\d+)(?:\s*marks?)?\s*\)|\b(?P<suffix>\d+)\s+marks?\b|\bmarks?\s*:\s*(?P<prefix>\d+)\b)",
    re.IGNORECASE,
)


class QuestionParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.hierarchy_parser = QuestionHierarchyParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str) -> list[Question]:
        # Resolve hierarchy before adapting to the flat legacy evaluator. This
        # prevents one parent (Q4) plus its a/b rows or an OR block from being
        # emitted as duplicate top-level Question objects.
        hierarchical = self.hierarchy_parser.parse(text)
        # A canonical top-level set is authoritative even when PDF table
        # extraction loses visible a/b or OR labels. Falling back in that case
        # was the live Q4 bug: the permissive legacy parser re-read a marks
        # column as an additional Q4.
        if hierarchical:
            self._log_canonical_debug(hierarchical)
            return self._adapt_hierarchy(hierarchical)
        questions = []
        seen_ids: set[QuestionId] = set()
        for section in self.section_parser.parse(text):
            if section.question_id in seen_ids:
                first = next(item for item in questions if item.question_id == section.question_id)
                raise ValueError(
                    f"Duplicate question ID: {section.question_id}; legacy fallback source blocks differ. "
                    f"first={first.question_text[:100]!r}; second={section.text[:100]!r}"
                )
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

    def _log_canonical_debug(self, hierarchical) -> None:
        self.logger.info("RAW PARSER OUTPUT: count=%s ids=%s", len(hierarchical), [item.id for item in hierarchical])
        for index, item in enumerate(hierarchical):
            self.logger.info(
                "CANONICAL QUESTION index=%s id=%s children=%s alternative_group=%s text=%r",
                index, item.id, [child.id for child in item.subquestions], item.alternative_group, item.text[:100],
            )

    def _adapt_hierarchy(self, hierarchical) -> list[Question]:
        questions: list[Question] = []
        for parent in hierarchical:
            parent_id = QuestionId(int(parent.number))
            if parent.subquestions:
                for child in parent.subquestions:
                    question_text, max_marks = self._extract_marks(child.text)
                    if not question_text:
                        raise ValueError(f"Question {child.id} has empty text")
                    questions.append(Question(
                        QuestionId(int(parent.number), child.label),
                        int(parent.number),
                        question_text,
                        max_marks,
                        parent_id=parent_id,
                        subpart=child.label,
                        alternative_group=parent.alternative_group,
                    ))
                continue
            question_text, max_marks = self._extract_marks(parent.text)
            if not question_text:
                raise ValueError(f"Question {parent.id} has empty text")
            questions.append(Question(
                parent_id,
                int(parent.number),
                question_text,
                max_marks,
                alternative_group=parent.alternative_group,
            ))
        self.logger.info("Canonical questions adapted for legacy evaluation: %s", len(questions))
        return questions

    @staticmethod
    def _extract_marks(text: str) -> tuple[str, int | None]:
        match = MARKS_PATTERN.search(text)
        if match is None:
            return text.strip(), None
        marks = next(int(value) for value in match.groupdict().values() if value is not None)
        return MARKS_PATTERN.sub("", text, count=1).strip(), marks
