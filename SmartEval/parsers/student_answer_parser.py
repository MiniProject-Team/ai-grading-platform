from __future__ import annotations

import logging
import re

from domain.entities.student_answer import StudentAnswer

from .section_parser import NumberedSectionParser


class StudentAnswerParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str, expected_question_ids: list[QuestionId] | None = None) -> list[StudentAnswer]:
        normalized = self._normalize_ocr_headings(text)
        sections = self.section_parser.parse(normalized)
        if not sections:
            candidates = [line.strip()[:80] for line in text.splitlines() if re.match(r"\s*(?:q|ans|answer|\d+\s*[.)])", line, re.I)][:12]
            self.logger.warning(
                "Student OCR contained no usable answer headings: text_length=%s heading_candidates=%s",
                len(text), candidates,
            )
            if expected_question_ids:
                return self._sequential_fallback(text, expected_question_ids)
            raise ValueError("No numbered student answers found")
        # Multiple subanswer labels under one top-level question are joined for
        # the current flat evaluator; no duplicate parent objects are emitted.
        grouped: dict[QuestionId, list[str]] = {}
        for section in sections:
            grouped.setdefault(section.question_id, []).append(section.text)
        answers = [StudentAnswer(question_id, "\n".join(parts), "explicit_heading", 0.97) for question_id, parts in grouped.items()]
        if len({answer.question_id for answer in answers}) != len(answers):
            raise ValueError("Duplicate question IDs in student answers")
        self.logger.info("Student answers detected: %s", len(answers))
        return answers

    def _sequential_fallback(self, text: str, expected_question_ids: list[QuestionId]) -> list[StudentAnswer]:
        """Conservative fallback when handwriting OCR loses all labels.

        Paragraph blocks are assigned in paper order only; content is never
        created or discarded and the low confidence remains visible downstream.
        """
        blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
        if not blocks:
            raise ValueError("No student answer content was extracted")
        count = min(len(blocks), len(expected_question_ids))
        # Preserve every block by appending any overflow to the final segment.
        segments = blocks[:count]
        if len(blocks) > count:
            segments[-1] = "\n\n".join(blocks[count - 1:])
        answers = [StudentAnswer(expected_question_ids[index], segment, "sequential_fallback", 0.35)
                   for index, segment in enumerate(segments)]
        self.logger.warning("Student answers mapped by sequential fallback: count=%s ids=%s", len(answers), [str(item.question_id) for item in answers])
        return answers

    @staticmethod
    def _normalize_ocr_headings(text: str) -> str:
        """Normalize only heading labels, never the handwritten answer body."""
        lines: list[str] = []
        for line in text.splitlines():
            # Common handwritten/OCR variants: Ans 1, Answer No. 1, Ql.
            line = re.sub(r"^(\s*)(?:ans(?:wer)?\s*(?:no\.?|number)?\s*[:.-]?\s*)([0-9Il]+)\b", r"\1Q\2 ", line, flags=re.I)
            line = re.sub(r"^(\s*)q\s*[.]?\s*([Il])(?=\s*[.):]|\s*$)", r"\1Q1", line, flags=re.I)
            lines.append(line)
        return "\n".join(lines)
