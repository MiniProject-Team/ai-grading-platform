from __future__ import annotations

from pathlib import Path

from domain.entities.evaluation_result import EvaluationResult
from evaluation.evaluation_engine import EvaluationEngine

from .input_pipeline import InputAnalysis, InputPipeline


class EvaluationPipeline:
    def __init__(self, input_pipeline: InputPipeline, evaluation_engine: EvaluationEngine) -> None:
        self.input_pipeline = input_pipeline
        self.evaluation_engine = evaluation_engine

    def run(self, question_paper: Path, model_answer: Path, student_text: Path) -> tuple[InputAnalysis, list[EvaluationResult]]:
        analysis = self.input_pipeline.run(question_paper, model_answer, student_text)
        return analysis, [self.evaluation_engine.evaluate(item) for item in analysis.items]
