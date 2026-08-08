"""Phase A entities shared by future SmartEval phases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class InputKind(str, Enum):
    QUESTION_PAPER = "question_paper"
    MODEL_ANSWER = "model_answer"
    STUDENT_OCR = "student_ocr"


@dataclass(frozen=True, slots=True)
class InputDocument:
    kind: InputKind
    source: Path
    text: str


@dataclass(frozen=True, slots=True)
class EvaluationInputs:
    question_paper: InputDocument
    model_answer: InputDocument
    student_ocr: InputDocument
