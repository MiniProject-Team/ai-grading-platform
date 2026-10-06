"""Phase 4 application workflow. It stops after structured answer mapping."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

from config.settings import Settings
from domain.entities.evaluation_item import EvaluationItem
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from parsers.model_answer_parser import ModelAnswerParser
from parsers.question_parser import QuestionParser
from parsers.student_answer_parser import StudentAnswerParser
from services.answer_mapping_service import AnswerMappingService
from services.input_manager import InputManager
from .progress import report_progress


@dataclass(frozen=True, slots=True)
class InputAnalysis:
    questions: list[Question]
    model_answers: list[ModelAnswer]
    student_answers: list[StudentAnswer]
    items: list[EvaluationItem]


class InputPipeline:
    def __init__(
        self,
        settings: Settings,
        input_manager: InputManager | None = None,
        question_parser: QuestionParser | None = None,
        model_parser: ModelAnswerParser | None = None,
        student_parser: StudentAnswerParser | None = None,
        mapper: AnswerMappingService | None = None,
    ) -> None:
        self.settings = settings
        self.input_manager = input_manager or InputManager()
        self.question_parser = question_parser or QuestionParser()
        self.model_parser = model_parser or ModelAnswerParser()
        self.student_parser = student_parser or StudentAnswerParser()
        self.mapper = mapper or AnswerMappingService()
        self.logger = logging.getLogger("smarteval")

    def run(self, question_paper: Path, model_answer: Path, student_text: Path) -> InputAnalysis:
        report_progress("uploading", "Reading the question paper and model answers.")
        question_text, model_answer_text = self.input_manager.load_teacher_inputs(question_paper, model_answer)
        questions = self.question_parser.parse(question_text)
        model_answers = self.model_parser.parse(model_answer_text)
        report_progress("reading", "Reading handwritten answers from the student sheet.")
        student_text_value = self.input_manager.load_student_text(student_text)
        self.logger.info("[OCR DEBUG] StudentAnswerParser input length: %s", len(student_text_value))
        if len(student_text_value) <= 2000:
            self.logger.info("[OCR DEBUG] Exact StudentAnswerParser input:\n%s", student_text_value)
        else:
            self.logger.info("[OCR DEBUG] StudentAnswerParser input preview (first 2000 characters):\n%s", student_text_value[:2000])
        debug_directory = Path(__file__).resolve().parents[1] / "outputs" / "debug"
        if debug_directory.is_dir():
            parser_input_path = debug_directory / "latest_student_parser_input.txt"
            parser_input_path.write_text(student_text_value, encoding="utf-8")
            self.logger.info("[OCR DEBUG] Exact StudentAnswerParser input saved to: %s", parser_input_path)
        student_answers = self.student_parser.parse(
            student_text_value,
            expected_question_ids=[question.question_id for question in questions],
        )
        report_progress("analyzing", f"Identified {len(student_answers)} student answers. Matching them to questions.")
        self.logger.info(
            "[OCR DEBUG] Parsed student answers: %s",
            [(str(answer.question_id), len(answer.answer_text)) for answer in student_answers],
        )
        return InputAnalysis(questions, model_answers, student_answers, self.mapper.map(questions, model_answers, student_answers))
