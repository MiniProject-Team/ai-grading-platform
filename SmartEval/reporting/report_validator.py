from __future__ import annotations

from math import isclose

from domain.entities.evaluation_report import EvaluationReport

from .exceptions import ReportValidationError


class ReportValidator:
    def validate(self, report: EvaluationReport) -> None:
        question_results = report.question_results
        if report.status == "failed":
            self._validate_failed_report(report)
            return
        if not question_results:
            raise ReportValidationError("Evaluation report must contain at least one question result")
        question_ids = [result.question_id for result in question_results]
        if len(set(question_ids)) != len(question_ids):
            raise ReportValidationError("Evaluation report contains duplicate question IDs")

        awarded_marks = 0.0
        evaluated_maximum = 0
        exam_maximum = 0
        evaluated_questions = 0
        missing_model_answers = 0
        unanswered_questions = 0
        partially_evaluated = False
        for result in question_results:
            marks = result.marks
            if marks.max_marks != result.max_marks:
                raise ReportValidationError(f"{result.question_id} maximum marks do not match")
            if marks.max_marks is not None:
                if marks.max_marks <= 0:
                    raise ReportValidationError(f"{result.question_id} maximum marks must be positive")
                exam_maximum += marks.max_marks
            if marks.marks_awarded is None:
                partially_evaluated = True
            else:
                if marks.max_marks is None:
                    raise ReportValidationError(f"{result.question_id} has awarded marks without maximum marks")
                if not 0 <= marks.marks_awarded <= marks.max_marks:
                    raise ReportValidationError(f"{result.question_id} awarded marks are outside the valid range")
                if marks.percentage is None or not 0 <= marks.percentage <= 100:
                    raise ReportValidationError(f"{result.question_id} percentage is outside the valid range")
                awarded_marks += marks.marks_awarded
                evaluated_maximum += marks.max_marks
                evaluated_questions += 1
            if result.evaluation.status == "model_answer_missing":
                missing_model_answers += 1
            if result.evaluation.status == "no_answer":
                unanswered_questions += 1

        summary = report.summary
        expected_totals = (
            (summary.total_questions, len(question_results)),
            (summary.evaluated_questions, evaluated_questions),
            (summary.missing_model_answers, missing_model_answers),
            (summary.unanswered_questions, unanswered_questions),
            (summary.evaluated_maximum_marks, evaluated_maximum),
            (summary.exam_maximum_marks, exam_maximum),
        )
        if any(actual != expected for actual, expected in expected_totals):
            raise ReportValidationError("Report summary totals do not match question results")
        if not isclose(summary.awarded_marks, awarded_marks, rel_tol=0, abs_tol=1e-9):
            raise ReportValidationError("Report awarded marks do not match question results")
        expected_percentage = round(awarded_marks / evaluated_maximum * 100, 2) if evaluated_maximum else None
        if summary.percentage is None and expected_percentage is not None:
            raise ReportValidationError("Report percentage is missing")
        if summary.percentage is not None and (not 0 <= summary.percentage <= 100 or not isclose(summary.percentage, expected_percentage, rel_tol=0, abs_tol=0.01)):
            raise ReportValidationError("Report percentage does not match evaluated marks")
        partially_evaluated = partially_evaluated or report.metadata.get("ocr_status") == "partially_processed"
        expected_status = "partially_evaluated" if partially_evaluated else "complete"
        if report.status != expected_status:
            raise ReportValidationError(f"Report status must be '{expected_status}'")

    @staticmethod
    def _validate_failed_report(report: EvaluationReport) -> None:
        if report.question_results:
            raise ReportValidationError("Failed reports cannot contain question results")
        summary = report.summary
        if any((
            summary.total_questions,
            summary.evaluated_questions,
            summary.unanswered_questions,
            summary.missing_model_answers,
            summary.awarded_marks,
            summary.evaluated_maximum_marks,
            summary.exam_maximum_marks,
        )) or summary.percentage is not None:
            raise ReportValidationError("Failed report summary must contain only zero or unavailable values")
        if not report.warnings:
            raise ReportValidationError("Failed report must include an explicit warning")
