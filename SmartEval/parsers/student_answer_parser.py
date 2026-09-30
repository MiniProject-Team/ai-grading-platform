from __future__ import annotations

import logging
import re

from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId

from .section_parser import NumberedSectionParser


HEADING_PATTERN = re.compile(
    r"^\s*(?:(?P<prefix>q(?:uestion)?|ans(?:wer)?(?:\s+(?:no\.?|number))?)\s*\.?\s*)?"
    r"(?P<number>\d+)\s*"
    r"(?:(?:\(\s*(?P<subpart_paren>[a-z])\s*\))|(?:[.)]\s*(?P<subpart_delimited>[a-z])(?=[\s.)]|$)\s*[.)]?))?"
    r"(?P<bare_delimiter>[.):])?\s*(?:[:.-]\s*)?(?P<body>.*)$",
    re.IGNORECASE,
)


class StudentAnswerParser:
    def __init__(self, section_parser: NumberedSectionParser | None = None) -> None:
        self.section_parser = section_parser or NumberedSectionParser()
        self.logger = logging.getLogger("smarteval")

    def parse(self, text: str, expected_question_ids: list[QuestionId] | None = None) -> list[StudentAnswer]:
        expected = set(expected_question_ids) if expected_question_ids is not None else None
        answers: list[StudentAnswer] = []
        current_id: QuestionId | None = None
        current_lines: list[str] = []
        saw_heading_candidate = False

        for line in text.splitlines():
            match = HEADING_PATTERN.match(line)
            candidate = self._candidate_id(match) if match else None
            heading_like = bool(match and self._is_heading_like(match))
            if heading_like:
                saw_heading_candidate = True
            if candidate is not None and self._accept_candidate(candidate, expected):
                if current_id is not None:
                    answers.append(self._build_answer(current_id, current_lines))
                current_id = candidate
                current_lines = [match.group("body").strip()] if match.group("body").strip() else []
                continue
            # A bare numbered list item is not a parent answer heading when
            # the paper expects subparts. Require Q/Question/Answer evidence.
            if heading_like and match.group("prefix") and candidate is not None and candidate.subpart is None and expected:
                parent_expected = any(
                    item.number == candidate.number and item.subpart is not None
                    for item in expected
                )
                if parent_expected:
                    if current_id is not None:
                        answers.append(self._build_answer(current_id, current_lines))
                    current_id = candidate
                    current_lines = [match.group("body").strip()] if match.group("body").strip() else []
                    continue
            if current_id is not None:
                current_lines.append(line)

        if current_id is not None:
            answers.append(self._build_answer(current_id, current_lines))
        answers = [answer for answer in answers if answer.answer_text.strip()]
        if not answers:
            candidates = [line.strip()[:80] for line in text.splitlines() if self._looks_like_candidate(line)][:12]
            self.logger.warning(
                "Student OCR contained no usable answer headings: text_length=%s heading_candidates=%s",
                len(text), candidates,
            )
            if expected_question_ids and not saw_heading_candidate:
                return self._sequential_fallback(text, expected_question_ids)
            raise ValueError("No numbered student answers found")
        if len({answer.question_id for answer in answers}) != len(answers):
            raise ValueError("Duplicate question IDs in student answers")
        self.logger.info("Student answers detected: %s ids=%s", len(answers), [str(answer.question_id) for answer in answers])
        return answers

    @staticmethod
    def _candidate_id(match: re.Match[str] | None) -> QuestionId | None:
        if match is None:
            return None
        subpart = match.group("subpart_paren") or match.group("subpart_delimited")
        if subpart is None and not match.group("prefix") and not match.group("bare_delimiter"):
            return None
        return QuestionId(int(match.group("number")), subpart.lower() if subpart else None)

    @staticmethod
    def _is_heading_like(match: re.Match[str]) -> bool:
        return bool(
            match.group("prefix")
            or match.group("subpart_paren")
            or match.group("subpart_delimited")
            or match.group("bare_delimiter")
        )

    @staticmethod
    def _accept_candidate(candidate: QuestionId, expected: set[QuestionId] | None) -> bool:
        return expected is None or candidate in expected

    @staticmethod
    def _build_answer(question_id: QuestionId, lines: list[str]) -> StudentAnswer:
        return StudentAnswer(question_id, "\n".join(lines).strip(), "explicit_heading", 0.97)

    @staticmethod
    def _looks_like_candidate(line: str) -> bool:
        match = HEADING_PATTERN.match(line)
        return bool(match and StudentAnswerParser._is_heading_like(match))

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

