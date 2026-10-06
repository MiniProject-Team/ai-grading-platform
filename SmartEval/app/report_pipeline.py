from __future__ import annotations

from pathlib import Path
from typing import Callable

from domain.entities.evaluation_report import EvaluationReport, ExamInformation, StudentInformation
from reporting.evaluation_report_generator import EvaluationReportGenerator

from .feedback_pipeline import FeedbackPipeline
from .progress import report_progress


class ReportPipeline:
    """Compose the completed evaluation phases into a final Phase 8 report."""

    def __init__(self, feedback_pipeline: FeedbackPipeline, report_generator: EvaluationReportGenerator) -> None:
        self.feedback_pipeline = feedback_pipeline
        self.report_generator = report_generator

    def run(
        self,
        question_paper: Path,
        model_answer: Path,
        student_text: Path,
        *,
        report_id: str | None = None,
        student_information: StudentInformation | None = None,
        exam_information: ExamInformation | None = None,
        additional_warnings: tuple[str, ...] = (),
        metadata: dict[str, str] | None = None,
        post_input_context: Callable[[], tuple[tuple[str, ...], dict[str, str]]] | None = None,
    ) -> EvaluationReport:
        analysis, evaluations, marks, total_marks, feedback = self.feedback_pipeline.run(
            question_paper,
            model_answer,
            student_text,
        )
        report_progress("report", "Preparing the final evaluation report.")
        if post_input_context is not None:
            provider_warnings, provider_metadata = post_input_context()
            additional_warnings = tuple(dict.fromkeys((*additional_warnings, *provider_warnings)))
            metadata = {**(metadata or {}), **provider_metadata}
        return self.report_generator.generate(
            analysis.items,
            evaluations,
            marks,
            feedback,
            total_marks,
            report_id=report_id,
            student_information=student_information,
            exam_information=exam_information,
            additional_warnings=additional_warnings,
            metadata=metadata,
        )
