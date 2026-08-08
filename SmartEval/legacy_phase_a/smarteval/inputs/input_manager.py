"""Phase A orchestration: validate and load the three SmartEval inputs."""

from __future__ import annotations

import logging
from pathlib import Path

from smarteval.core.entities import EvaluationInputs, InputDocument, InputKind
from smarteval.core.exceptions import InputValidationError

from .json_loader import JsonInputLoader
from .text_loader import TextInputLoader


class InputManager:
    def __init__(self, text_loader: TextInputLoader | None = None, json_loader: JsonInputLoader | None = None) -> None:
        self.text_loader = text_loader or TextInputLoader()
        self.json_loader = json_loader or JsonInputLoader()
        self.logger = logging.getLogger("smarteval")

    def load(self, question_paper: Path, model_answer: Path, student_ocr: Path) -> EvaluationInputs:
        return EvaluationInputs(
            question_paper=self._load_document(InputKind.QUESTION_PAPER, question_paper),
            model_answer=self._load_document(InputKind.MODEL_ANSWER, model_answer),
            student_ocr=self._load_document(InputKind.STUDENT_OCR, student_ocr),
        )

    def _load_document(self, kind: InputKind, source: Path) -> InputDocument:
        source = source.resolve()
        if not source.exists():
            raise InputValidationError(f"{kind.value} source not found: {source}")
        if source.is_dir():
            text = self.text_loader.load(source)
        elif source.suffix.lower() == ".txt":
            text = self.text_loader.load(source)
        elif source.suffix.lower() == ".json":
            text = self.json_loader.load(source)
        else:
            raise InputValidationError(f"Unsupported {kind.value} file type: {source.suffix}")
        if not text:
            raise InputValidationError(f"{kind.value} input is empty: {source}")
        self.logger.info("Loaded %s input from %s", kind.value, source)
        return InputDocument(kind=kind, source=source, text=text)
