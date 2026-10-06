from __future__ import annotations

from pathlib import Path

from domain.entities.evaluation_result import EvaluationResult
from evaluation.evaluation_engine import EvaluationEngine

from .input_pipeline import InputAnalysis, InputPipeline
from .progress import report_progress


class EvaluationPipeline:
    def __init__(self, input_pipeline: InputPipeline, evaluation_engine: EvaluationEngine) -> None:
        self.input_pipeline = input_pipeline
        self.evaluation_engine = evaluation_engine

    def run(self, question_paper: Path, model_answer: Path, student_text: Path) -> tuple[InputAnalysis, list[EvaluationResult]]:
        analysis = self.input_pipeline.run(question_paper, model_answer, student_text)
        results = []
        for index, item in enumerate(analysis.items, start=1):
            report_progress("analyzing", f"Evaluating answer {index} of {len(analysis.items)} ({item.question.question_id}).")
            results.append(self.evaluation_engine.evaluate(item))
        return analysis, results
