from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.input_pipeline import InputAnalysis
from app.report_pipeline import ReportPipeline
from reporting.evaluation_report_generator import EvaluationReportGenerator
from reporting.json_report_exporter import JsonReportExporter
from reporting.text_report_exporter import TextReportExporter

from report_fixtures import report_inputs


class _FeedbackPipeline:
    def run(self, question_paper, model_answer, student_text):
        items, evaluations, marks, feedback, total = report_inputs()
        analysis = InputAnalysis(
            questions=[item.question for item in items],
            model_answers=[item.model_answer for item in items if item.model_answer],
            student_answers=[item.student_answer for item in items],
            items=items,
        )
        return analysis, evaluations, marks, total, feedback


class CompleteEvaluationReportTests(unittest.TestCase):
    def test_mixed_evaluation_produces_consistent_partial_report_and_exports(self):
        report = ReportPipeline(_FeedbackPipeline(), EvaluationReportGenerator()).run(
            Path("questions.txt"),
            Path("model_answers.txt"),
            Path("student_answers.txt"),
            report_id="evaluation_integration",
        )

        self.assertEqual(len(report.question_results), 5)
        self.assertEqual(report.status, "partially_evaluated")
        self.assertEqual(report.summary.awarded_marks, 23.0)
        self.assertEqual(report.summary.evaluated_maximum_marks, 40)
        self.assertEqual(report.summary.exam_maximum_marks, 50)
        self.assertEqual(report.summary.unanswered_questions, 1)
        self.assertEqual(report.summary.missing_model_answers, 1)
        self.assertIsNone(report.question_results[4].marks.marks_awarded)
        self.assertTrue(any("Q4 has no detected student answer" in warning for warning in report.warnings))
        self.assertTrue(any("Q5 could not be evaluated" in warning for warning in report.warnings))

        with TemporaryDirectory() as directory:
            json_path = JsonReportExporter(Path(directory)).export(report)
            text_path = TextReportExporter(Path(directory)).export(report)
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
