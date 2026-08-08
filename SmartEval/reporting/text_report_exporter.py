from __future__ import annotations

import logging
from pathlib import Path

from domain.entities.evaluation_report import EvaluationReport


class TextReportExporter:
    def __init__(self, reports_directory: Path) -> None:
        self.reports_directory = reports_directory
        self.logger = logging.getLogger("smarteval")

    def export(self, report: EvaluationReport) -> Path:
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        output_path = self.reports_directory / f"{self._file_stem(report.report_id)}.txt"
        output_path.write_text(self._render(report), encoding="utf-8")
        self.logger.info("Text report exported: %s", output_path)
        return output_path

    @staticmethod
    def _file_stem(report_id: str) -> str:
        return report_id if report_id.startswith("evaluation_") else f"evaluation_{report_id}"

    @staticmethod
    def _render(report: EvaluationReport) -> str:
        summary = report.summary
        lines = [
            "=" * 40,
            "SMART EVAL - EVALUATION REPORT",
            "=" * 40,
            "",
            "Status:",
            report.status.replace("_", " ").upper(),
            "",
            "Total Marks:",
            f"{summary.awarded_marks} / {summary.evaluated_maximum_marks}",
            "",
            "Percentage:",
            "Unavailable" if summary.percentage is None else f"{summary.percentage}%",
            "",
            "-" * 40,
            "QUESTION-WISE EVALUATION",
            "-" * 40,
        ]
        for result in report.question_results:
            awarded = "Unavailable" if result.marks.marks_awarded is None else str(result.marks.marks_awarded)
            maximum = "Unavailable" if result.marks.max_marks is None else str(result.marks.max_marks)
            lines.extend([
                "",
                str(result.question_id),
                "Question:",
                result.question_text,
                "",
                "Marks:",
                f"{awarded} / {maximum}",
                "",
                "Status:",
                result.evaluation.status.replace("_", " ").upper(),
                "",
                "Feedback:",
                result.feedback.overall_feedback,
                "-" * 40,
            ])
        lines.extend([
            "SUMMARY",
            "-" * 40,
            f"Questions: {summary.total_questions}",
            f"Evaluated: {summary.evaluated_questions}",
            f"Unanswered: {summary.unanswered_questions}",
            f"Total: {summary.awarded_marks} / {summary.evaluated_maximum_marks}",
            f"Exam Maximum: {summary.exam_maximum_marks}",
            "Percentage: Unavailable" if summary.percentage is None else f"Percentage: {summary.percentage}%",
        ])
        if report.warnings:
            lines.extend(["", "WARNINGS"])
            lines.extend(f"- {warning}" for warning in report.warnings)
        lines.extend(["", "=" * 40, ""])
        return "\n".join(lines)
