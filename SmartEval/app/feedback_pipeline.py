from __future__ import annotations

from pathlib import Path

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.entities.total_marks_result import TotalMarksResult
from evaluation.marks.marks_calculator import MarksCalculator
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from feedback.feedback_service import FeedbackService

from .evaluation_pipeline import EvaluationPipeline
from .input_pipeline import InputAnalysis


class FeedbackPipeline:
    """Run Phases 4-7 once and retain each question's associated results."""

    def __init__(
        self,
        evaluation_pipeline: EvaluationPipeline,
        marks_calculator: MarksCalculator,
        total_calculator: TotalMarksCalculator,
        feedback_service: FeedbackService,
    ) -> None:
        self.evaluation_pipeline = evaluation_pipeline
        self.marks_calculator = marks_calculator
        self.total_calculator = total_calculator
        self.feedback_service = feedback_service

    def run(
        self,
        question_paper: Path,
        model_answer: Path,
        student_text: Path,
    ) -> tuple[InputAnalysis, list[EvaluationResult], list[MarksResult], TotalMarksResult, list[FeedbackResult]]:
        analysis, evaluations = self.evaluation_pipeline.run(question_paper, model_answer, student_text)
        marks = [self.marks_calculator.calculate(item.question, result) for item, result in zip(analysis.items, evaluations, strict=True)]
        total = self.total_calculator.calculate(marks)
        feedback = self.feedback_service.generate(analysis.items, evaluations, marks)
        return analysis, evaluations, marks, total, feedback
