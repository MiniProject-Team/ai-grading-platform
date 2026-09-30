from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reporting.exceptions import ReportValidationError
from reporting.json_report_exporter import JsonReportExporter
from reporting.report_builder import ReportBuilder
from reporting.report_validator import ReportValidator
from reporting.statistics_builder import StatisticsBuilder
from reporting.summary_builder import SummaryBuilder
from reporting.text_report_exporter import TextReportExporter

from report_fixtures import build_report, report_inputs


class ReportBuilderTests(unittest.TestCase):
    def test_combines_every_phase_result_by_question_id(self):
        items, evaluations, marks, feedback, _ = report_inputs()
        question_results = ReportBuilder().build_question_results(items, evaluations, marks, feedback)
        self.assertEqual(len(question_results), 5)
        self.assertEqual(str(question_results[1].question_id), "Q2")
        self.assertEqual(question_results[1].marks.marks_awarded, 8.0)

    def test_rejects_missing_result(self):
        items, evaluations, marks, feedback, _ = report_inputs()
        with self.assertRaises(ReportValidationError):
            ReportBuilder().build_question_results(items, evaluations[:-1], marks, feedback)


class SummaryBuilderTests(unittest.TestCase):
    def test_uses_authoritative_total_marks_result(self):
        _, _, _, _, total = report_inputs()
        summary = SummaryBuilder().build(total, 5)
        self.assertEqual(summary.awarded_marks, 23.0)
        self.assertEqual(summary.evaluated_maximum_marks, 40)
        self.assertEqual(summary.exam_maximum_marks, 50)
        self.assertEqual(summary.percentage, 46.0)


class StatisticsBuilderTests(unittest.TestCase):
    def test_calculates_statuses_and_score_extremes(self):
        report = build_report()
        statistics = StatisticsBuilder().build(list(report.question_results))
        self.assertEqual(statistics.status_distribution["correct"], 1)
        self.assertEqual(statistics.status_distribution["no_answer"], 1)
        self.assertEqual(str(statistics.highest_score_question), "Q1")
        self.assertEqual(str(statistics.lowest_score_question), "Q4")


class ReportValidatorTests(unittest.TestCase):
    def test_rejects_status_that_hides_unavailable_questions(self):
        report = build_report()
        with self.assertRaisesRegex(ReportValidationError, "partially_evaluated"):
            ReportValidator().validate(replace(report, status="complete"))


class ReportExporterTests(unittest.TestCase):
    def test_json_exporter_serializes_api_ready_report(self):
        report = build_report()
        with TemporaryDirectory() as directory:
            output = JsonReportExporter(Path(directory)).export(report)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["report_id"], "evaluation_test")
        self.assertEqual(payload["summary"]["evaluated_maximum_marks"], 40)
        self.assertEqual(payload["question_results"][4]["marks"]["awarded"], None)

    def test_text_exporter_renders_human_readable_summary(self):
        report = build_report()
        with TemporaryDirectory() as directory:
            output = TextReportExporter(Path(directory)).export(report)
            text = output.read_text(encoding="utf-8")
        self.assertIn("SMART EVAL - EVALUATION REPORT", text)
        self.assertIn("PARTIALLY EVALUATED", text)
        self.assertIn("Q5", text)
        self.assertIn("Exam Maximum: 50", text)

    def test_exporters_prefix_custom_report_ids(self):
        report = build_report()
        report = replace(report, report_id="001")
        with TemporaryDirectory() as directory:
            json_path = JsonReportExporter(Path(directory)).export(report)
            text_path = TextReportExporter(Path(directory)).export(report)
        self.assertEqual(json_path.name, "evaluation_001.json")
        self.assertEqual(text_path.name, "evaluation_001.txt")
