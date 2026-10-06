from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from app.progress import progress_callback

from config.settings import Settings
from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult
from integration.evaluation_service import EvaluationRequest, EvaluationService
from integration.smarthtr_client import OCRPageResult, SmartHTROCRResult
from integration.student_text_provider import SmartHTRIntegrationService, SmartHTRStudentTextProvider, StudentTextExtractionError


QUESTION_TEXT = "Q1. Define Artificial Intelligence. (10 Marks)\nQ2. Explain Machine Learning. (10 Marks)"
MODEL_TEXT = "Q1. Artificial Intelligence is the simulation of human intelligence.\nQ2. Machine Learning enables systems to learn from data."
STUDENT_TEXT = "Q1. Artificial Intelligence simulates human intelligence.\nQ2. Machine Learning allows systems to learn from data."


class _Client:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0

    def recognize(self, student_sheet):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class _EvaluationEngine:
    def evaluate(self, item: EvaluationItem) -> EvaluationResult:
        question_id = item.question.question_id
        if item.model_answer_missing:
            return EvaluationResult(question_id, None, None, None, None, "model_answer_missing", "model answer unavailable")
        if item.student_answer_missing:
            return EvaluationResult(question_id, 0.0, 0.0, 0.0, 0.0, "no_answer", "no student answer")
        return EvaluationResult(question_id, .9, .9, .9, .9, "correct", "test")


def ocr_result(text=STUDENT_TEXT, status="success", warnings=()):
    return SmartHTROCRResult(
        status=status,
        pages=(OCRPageResult(1, text),),
        full_text=text,
        metadata={"page_count": 1},
        warnings=warnings,
    )


class EndToEndEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.question_paper = self.root / "questions.txt"
        self.model_answer = self.root / "model_answers.txt"
        self.student_sheet = self.root / "student_sheet.pdf"
        self.question_paper.write_text(QUESTION_TEXT, encoding="utf-8")
        self.model_answer.write_text(MODEL_TEXT, encoding="utf-8")
        self.student_sheet.write_bytes(b"fake pdf input")
        self.settings = Settings(log_directory=self.root / "logs", output_directory=self.root / "outputs")

    def tearDown(self):
        self.directory.cleanup()

    def service(self, client: _Client) -> EvaluationService:
        provider = SmartHTRStudentTextProvider(SmartHTRIntegrationService(client))
        return EvaluationService(self.settings, student_text_provider=provider, evaluation_engine=_EvaluationEngine())

    def request(self, **changes) -> EvaluationRequest:
        values = {
            "question_paper_path": self.question_paper,
            "model_answer_path": self.model_answer,
            "student_answer_sheet_path": self.student_sheet,
            "student_id": "student-1",
            "subject": "AI",
            "exam_name": "Midterm",
        }
        values.update(changes)
        return EvaluationRequest(**values)

    def test_complete_sheet_runs_ocr_through_final_report_and_exports(self):
        client = _Client(ocr_result())
        result = self.service(client).evaluate_and_export(self.request(report_id="001"))

        self.assertEqual(client.calls, 1)
        self.assertEqual(result.ocr_result.full_text, STUDENT_TEXT)
        self.assertEqual(result.report.status, "complete")
        self.assertEqual(result.report.summary.total_questions, 2)
        self.assertEqual(result.report.summary.evaluated_questions, 2)
        self.assertEqual(result.report.summary.awarded_marks, 18.0)
        self.assertTrue(result.json_report_path.exists())
        self.assertTrue(result.text_report_path.exists())
        self.assertEqual(result.json_report_path.name, "evaluation_001.json")

    def test_progress_follows_real_pipeline_stages(self):
        events = []
        token = progress_callback.set(lambda stage, message: events.append((stage, message)))
        try:
            result = self.service(_Client(ocr_result())).evaluate_and_export(self.request())
        finally:
            progress_callback.reset(token)
        self.assertEqual(result.report.status, "complete")
        stages = list(dict.fromkeys(stage for stage, _ in events))
        self.assertEqual(stages, ["uploading", "reading", "analyzing", "marks", "feedback", "report"])
        self.assertTrue(any("answer 2 of 2" in message for _, message in events))

    def test_missing_question_paper_returns_failed_report(self):
        report = self.service(_Client(ocr_result())).evaluate(self.request(question_paper_path=self.root / "missing.txt"))
        self.assertEqual(report.status, "failed")
        self.assertIn("Question paper was not found", report.warnings[0])

    def test_missing_model_answer_returns_failed_report(self):
        report = self.service(_Client(ocr_result())).evaluate(self.request(model_answer_path=self.root / "missing.txt"))
        self.assertEqual(report.status, "failed")
        self.assertIn("Model answer was not found", report.warnings[0])

    def test_missing_student_sheet_returns_failed_report(self):
        report = self.service(_Client(ocr_result())).evaluate(self.request(student_answer_sheet_path=self.root / "missing.pdf"))
        self.assertEqual(report.status, "failed")
        self.assertIn("Student answer sheet was not found", report.warnings[0])

    def test_smarthtr_failure_returns_explicit_failed_report(self):
        report = self.service(_Client(error=RuntimeError("ocr unavailable"))).evaluate(self.request())
        self.assertEqual(report.status, "failed")
        self.assertEqual(report.warnings, ("Student handwritten text extraction failed.",))

    def test_empty_ocr_result_stops_before_evaluation(self):
        report = self.service(_Client(ocr_result(text=""))).evaluate(self.request())
        self.assertEqual(report.status, "failed")
        self.assertEqual(report.warnings, ("No handwritten text was extracted from the student answer sheet.",))

    def test_partial_ocr_preserves_warning_and_marks_report_partial(self):
        client = _Client(ocr_result(status="partially_processed", warnings=("Page 3 could not be processed.",)))
        report = self.service(client).evaluate(self.request())
        self.assertEqual(report.status, "partially_evaluated")
        self.assertIn("Page 3 could not be processed.", report.warnings)
        self.assertEqual(report.metadata["ocr_status"], "partially_processed")

    def test_partial_ocr_can_be_configured_to_stop(self):
        provider = SmartHTRStudentTextProvider(
            SmartHTRIntegrationService(_Client(ocr_result(status="partially_processed"))),
            continue_on_partial=False,
        )
        with self.assertRaisesRegex(StudentTextExtractionError, "partially processed"):
            provider.get_text(self.student_sheet)

    def test_missing_student_answer_for_one_question_is_reported(self):
        partial_text = "Q1. Artificial Intelligence simulates human intelligence."
        report = self.service(_Client(ocr_result(text=partial_text))).evaluate(self.request())
        self.assertEqual(report.summary.unanswered_questions, 1)
        self.assertEqual(report.question_results[1].evaluation.status, "no_answer")
        self.assertTrue(any("Q2 has no detected student answer" in warning for warning in report.warnings))

    def test_missing_model_answer_for_one_question_is_partially_evaluated(self):
        self.model_answer.write_text("Q1. Artificial Intelligence is the simulation of human intelligence.", encoding="utf-8")
        report = self.service(_Client(ocr_result())).evaluate(self.request())
        self.assertEqual(report.status, "partially_evaluated")
        self.assertEqual(report.summary.missing_model_answers, 1)
        self.assertIsNone(report.question_results[1].marks.marks_awarded)
