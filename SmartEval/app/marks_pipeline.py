from __future__ import annotations

from pathlib import Path

from domain.entities.marks_result import MarksResult
from domain.entities.total_marks_result import TotalMarksResult
from evaluation.marks.marks_calculator import MarksCalculator
from evaluation.marks.total_marks_calculator import TotalMarksCalculator

from .evaluation_pipeline import EvaluationPipeline
from .input_pipeline import InputAnalysis


class MarksPipeline:
    def __init__(self, evaluation_pipeline: EvaluationPipeline, marks_calculator: MarksCalculator, total_calculator: TotalMarksCalculator) -> None:
        self.evaluation_pipeline = evaluation_pipeline
        self.marks_calculator = marks_calculator
        self.total_calculator = total_calculator

    def run(self, question_paper: Path, model_answer: Path, student_text: Path) -> tuple[InputAnalysis, list[MarksResult], TotalMarksResult]:
        analysis, evaluations = self.evaluation_pipeline.run(question_paper, model_answer, student_text)
        marks = [self.marks_calculator.calculate(item.question, result) for item, result in zip(analysis.items, evaluations)]
        return analysis, marks, self.total_calculator.calculate(marks, analysis.questions)
