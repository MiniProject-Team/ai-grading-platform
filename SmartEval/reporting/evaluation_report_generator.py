from __future__ import annotations

import logging
import time
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_report import (
    EvaluationReport,
    EvaluationStatistics,
    EvaluationSummary,
    ExamInformation,
    QuestionEvaluationResult,
    StudentInformation,
)
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.entities.total_marks_result import TotalMarksResult

from .report_builder import ReportBuilder
from .report_validator import ReportValidator
from .statistics_builder import StatisticsBuilder
from .summary_builder import SummaryBuilder


class EvaluationReportGenerator:
    def __init__(
        self,
        report_builder: ReportBuilder | None = None,
        summary_builder: SummaryBuilder | None = None,
        statistics_builder: StatisticsBuilder | None = None,
        validator: ReportValidator | None = None,
    ) -> None:
        self.report_builder = report_builder or ReportBuilder()
        self.summary_builder = summary_builder or SummaryBuilder()
        self.statistics_builder = statistics_builder or StatisticsBuilder()
        self.validator = validator or ReportValidator()
        self.logger = logging.getLogger("smarteval")

    def generate(
        self,
        items: list[EvaluationItem],
        evaluations: list[EvaluationResult],
        marks_results: list[MarksResult],
        feedback_results: list[FeedbackResult],
        total_marks: TotalMarksResult,
        *,
        report_id: str | None = None,
        student_information: StudentInformation | None = None,
        exam_information: ExamInformation | None = None,
        additional_warnings: tuple[str, ...] = (),
        metadata: dict[str, str] | None = None,
    ) -> EvaluationReport:
        started = time.perf_counter()
        self.logger.info("Report generation started for %s questions", len(items))
        question_results = self.report_builder.build_question_results(items, evaluations, marks_results, feedback_results)
        summary = self.summary_builder.build(total_marks, len(question_results))
        warnings = self._warnings(question_results, additional_warnings)
        report = EvaluationReport(
            report_id=report_id or f"evaluation_{uuid4().hex}",
            status="partially_evaluated" if total_marks.unevaluated_questions or (metadata or {}).get("ocr_status") == "partially_processed" else "complete",
            question_results=tuple(question_results),
            summary=summary,
            statistics=self.statistics_builder.build(question_results),
            warnings=warnings,
            student_information=student_information,
            exam_information=exam_information,
            top_strengths=self._common_feedback(question_results, "strengths"),
            common_weaknesses=self._common_feedback(question_results, "weaknesses"),
            overall_improvement_suggestions=self._common_feedback(question_results, "suggestions"),
            metadata={"generated_at": datetime.now(timezone.utc).isoformat(), **(metadata or {})},
        )
        self.validator.validate(report)
        self.logger.info(
            "Report validated: status=%s evaluated=%s warnings=%s duration=%.2fs",
            report.status,
            summary.evaluated_questions,
            len(warnings),
            time.perf_counter() - started,
        )
        return report

    def failed_report(
        self,
        message: str,
        *,
        report_id: str | None = None,
        student_information: StudentInformation | None = None,
        exam_information: ExamInformation | None = None,
        metadata: dict[str, str] | None = None,
    ) -> EvaluationReport:
        report = EvaluationReport(
            report_id=report_id or f"evaluation_{uuid4().hex}",
            status="failed",
            question_results=(),
            summary=EvaluationSummary(0, 0, 0, 0, 0.0, 0, 0, None),
            statistics=EvaluationStatistics(None, None, None, None, None, None, None, {
                "correct": 0,
                "mostly_correct": 0,
                "partially_correct": 0,
                "irrelevant": 0,
                "no_answer": 0,
                "model_answer_missing": 0,
            }),
            warnings=(message,),
            student_information=student_information,
            exam_information=exam_information,
            metadata={"generated_at": datetime.now(timezone.utc).isoformat(), **(metadata or {})},
        )
        self.validator.validate(report)
        self.logger.warning("Failed report generated: %s", message)
        return report

    @staticmethod
    def _warnings(question_results: list[QuestionEvaluationResult], additional_warnings: tuple[str, ...]) -> tuple[str, ...]:
        warnings = list(additional_warnings)
        for result in question_results:
            question_id = result.question_id
            if result.evaluation.status == "model_answer_missing":
                warnings.append(f"{question_id} could not be evaluated because the model answer was missing.")
            if result.evaluation.status == "no_answer":
                warnings.append(f"{question_id} has no detected student answer.")
            if result.marks.max_marks is None:
                warnings.append(f"{question_id} marks could not be calculated because maximum marks were unavailable.")
        return tuple(dict.fromkeys(warnings))

    @staticmethod
    def _common_feedback(question_results: list[QuestionEvaluationResult], category: str) -> tuple[str, ...]:
        if category == "strengths":
            values = [value for result in question_results for value in result.feedback.strengths]
        elif category == "weaknesses":
            values = [value for result in question_results for value in (*result.feedback.missing_concepts, *result.feedback.weak_areas)]
        else:
            values = [value for result in question_results for value in result.feedback.improvement_suggestions]
        counts = Counter(values)
        return tuple(value for value, _ in counts.most_common(3))
