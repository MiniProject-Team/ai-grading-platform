"""Canonical hierarchical representation used before legacy evaluation adaption."""
from __future__ import annotations

from dataclasses import dataclass, field
import re

from parsers.section_parser import normalize_question_id


# Bare numeric headings are intentionally limited to ordinary question labels.
# This prevents table metadata such as a C.O. value of ``703.1`` from being
# interpreted as Q703 followed by a fake child question.
TOP = re.compile(r"^\s*(?:q(?:uestion)?\s*\.?)?\s*(\d{1,2})(?!\d)\s*(?:[.):]\s*)?(.*)$", re.I)
SUB = re.compile(r"^\s*(?:\(?\s*([a-z]|[ivxlcdm]+)\s*\)?[.)]|\(\s*([a-z]|[ivxlcdm]+)\s*\))\s*(.*)$", re.I)
OR = re.compile(r"^\s*(?:or|either|alternatively|internal\s+choice)\s*$", re.I)


@dataclass
class CanonicalSubquestion:
    id: str
    label: str
    text: str


@dataclass
class CanonicalQuestion:
    id: str
    number: str
    text: str = ""
    subquestions: list[CanonicalSubquestion] = field(default_factory=list)
    alternative_group: str | None = None


class QuestionHierarchyParser:
    def __init__(self, *, allow_bare_numbers: bool = True) -> None:
        self.allow_bare_numbers = allow_bare_numbers

    def parse(self, text: str, debug: bool = False) -> list[CanonicalQuestion]:
        questions: list[CanonicalQuestion] = []
        current: CanonicalQuestion | None = None
        pending_or = False
        group = 0
        seen: dict[str, CanonicalQuestion] = {}
        debug_lines: list[str] = []
        for raw in text.splitlines():
            line = re.sub(r"\s+", " ", raw).strip()
            if not line:
                continue
            if OR.match(line):
                pending_or = True
                continue
            top = TOP.match(line)
            # Numeric prose (e.g. "4 marks") is not a top-level question.
            is_top = bool(top and (
                line.lower().startswith(("q", "question"))
                or (self.allow_bare_numbers and re.match(r"^\d+\s*[.):]", line))
            ))
            if is_top:
                number, body = top.groups()
                identifier = normalize_question_id(number)
                inline_sub = SUB.match(body.strip())
                if identifier in seen:
                    existing = seen[identifier]
                    # Model-answer sheets often repeat the parent label for
                    # each child: Q4(a) ... then Q4(b) .... It is one parent,
                    # not two independent Q4 questions.
                    if inline_sub:
                        label, roman, child_text = inline_sub.groups()
                        label = (label or roman).lower()
                        child_id = normalize_question_id(f"{number}({label})")
                        if any(item.id == child_id for item in existing.subquestions):
                            raise ValueError(f"Duplicate subquestion ID: {child_id} (genuine independent subquestion)")
                        existing.subquestions.append(CanonicalSubquestion(child_id, label, child_text.strip()))
                        current = existing
                        continue
                    if not body.strip() or body.strip() in existing.text:
                        current = existing  # page continuation/repeated rendering
                        continue
                    raise ValueError(f"Duplicate question ID: {identifier} (genuine independent question)")
                current = CanonicalQuestion(identifier, number, "" if inline_sub else body.strip())
                if inline_sub:
                    label, roman, child_text = inline_sub.groups()
                    label = (label or roman).lower()
                    current.subquestions.append(CanonicalSubquestion(normalize_question_id(f"{number}({label})"), label, child_text.strip()))
                if pending_or:
                    group += 1
                    current.alternative_group = f"OR_{group}"
                    if questions:
                        questions[-1].alternative_group = current.alternative_group
                    pending_or = False
                questions.append(current); seen[identifier] = current
                debug_lines.append(f"RAW QUESTION BLOCK: {line}\nDETECTED NUMBER: {number}\nNORMALIZED ID: {identifier}")
                continue
            sub = SUB.match(line)
            if sub and current:
                label, roman, body = sub.groups()
                label = (label or roman).lower()
                child_id = normalize_question_id(f"{current.number}({label})")
                if any(item.id == child_id for item in current.subquestions):
                    raise ValueError(f"Duplicate subquestion ID: {child_id} (genuine independent subquestion)")
                current.subquestions.append(CanonicalSubquestion(child_id, label, body.strip()))
            elif current:
                if current.subquestions:
                    current.subquestions[-1].text = f"{current.subquestions[-1].text} {line}".strip()
                else:
                    current.text = f"{current.text} {line}".strip()
        if debug:
            print("\n".join(debug_lines + ["TOP-LEVEL QUESTIONS:"] + [q.id for q in questions] + ["DUPLICATES:\nNone"]))
        return questions
