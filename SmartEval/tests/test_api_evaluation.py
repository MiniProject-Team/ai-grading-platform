from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import unittest

from fastapi.testclient import TestClient

from api.app import _default_service_factory, create_app
from api.routes.evaluation import _failed_report_problem
from app.progress import report_progress
from config.settings import Settings
from integration.evaluation_service import EndToEndEvaluationResult
from reporting.evaluation_report_generator import EvaluationReportGenerator
from persistence.service import PersistedEvaluation

from tests.report_fixtures import build_report


PDF_BYTES = b"%PDF-1.4\nmock upload\n"


class _EvaluationService:
    def __init__(self, report=None, error: Exception | None = None):
        self.report = report
        self.error = error
        self.requests = []

    def evaluate_and_export(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return EndToEndEvaluationResult(
            report=self.report,
            ocr_result=None,
            json_report_path=Path("report.json"),
            text_report_path=Path("report.txt"),
        )


class _PersistenceService:
    def __init__(self):
        self.saved = []

    def persist(self, report, **kwargs):
        self.saved.append((report, kwargs))
        return PersistedEvaluation(report.report_id, report.status, report.to_dict())


class APIEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        root = Path(self.directory.name)
        self.settings = Settings(log_directory=root / "logs", output_directory=root / "outputs", temp_directory=root / "temp")
        self.complete_report = replace(build_report(), status="complete")
        self.partial_report = build_report()

    def tearDown(self):
        self.directory.cleanup()

    def client(self, service: _EvaluationService, settings: Settings | None = None) -> TestClient:
        persistence = _PersistenceService()
        return TestClient(create_app(
            settings or self.settings,
            evaluation_service_factory=lambda: service,
            persistence_service_factory=lambda: persistence,
        ))

    @staticmethod
    def files(**overrides):
        data = {
            "question_paper": ("questions.pdf", PDF_BYTES, "application/pdf"),
            "model_answer": ("answers.pdf", PDF_BYTES, "application/pdf"),
            "student_answer_sheet": ("student.pdf", PDF_BYTES, "application/pdf"),
        }
        data.update(overrides)
        return data

    def test_health_endpoint_does_not_require_evaluation_service(self):
        response = self.client(_EvaluationService(self.complete_report)).get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "SmartEval"})

    def test_progress_is_available_while_evaluation_is_running(self):
        entered = Event()
        release = Event()
        report = self.complete_report

        class BlockingService(_EvaluationService):
            def evaluate_and_export(self, request):
                report_progress("reading", "OCR reading attempt 1: 2,955 characters extracted.")
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("Test did not release evaluation")
                return super().evaluate_and_export(request)

        with self.client(BlockingService(report)) as client, ThreadPoolExecutor() as executor:
            future = executor.submit(client.post, "/api/v1/evaluate", files=self.files(), headers={"Idempotency-Key": "live-test"})
            try:
                self.assertTrue(entered.wait(5))
                response = client.get("/api/v1/evaluation-progress/live-test")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["stage"], "reading")
                self.assertIn("2,955", response.json()["message"])
                self.assertEqual(client.get("/api/v1/evaluation-progress/other-request").json()["status"], "pending")
            finally:
                release.set()
            self.assertEqual(future.result(timeout=5).status_code, 200)
            self.assertEqual(client.get("/api/v1/evaluation-progress/live-test").json()["status"], "complete")

    def test_failed_evaluation_finishes_progress(self):
        with self.client(_EvaluationService(error=RuntimeError("test failure"))) as client:
            response = client.post("/api/v1/evaluate", files=self.files(), headers={"Idempotency-Key": "failed-test"})
            self.assertEqual(response.status_code, 500)
            snapshot = client.get("/api/v1/evaluation-progress/failed-test").json()
            self.assertEqual(snapshot["status"], "failed")
            self.assertNotIn("test failure", snapshot["message"])

    def test_default_service_factory_reuses_one_smarthtr_client(self):
        factory = _default_service_factory(self.settings)
        first = factory()
        second = factory()
        first_client = first.student_text_provider.integration_service.client
        second_client = second.student_text_provider.integration_service.client
        self.assertIs(first_client, second_client)
        self.assertIsNot(first.student_text_provider, second.student_text_provider)

    def test_openapi_docs_endpoint_is_available(self):
        response = self.client(_EvaluationService(self.complete_report)).get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_missing_question_paper_returns_safe_validation_error(self):
        response = self.client(_EvaluationService(self.complete_report)).post(
            "/api/v1/evaluate",
            files={
                "model_answer": ("answers.pdf", PDF_BYTES, "application/pdf"),
                "student_answer_sheet": ("student.pdf", PDF_BYTES, "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_INPUT")

    def test_missing_model_answer_returns_safe_validation_error(self):
        response = self.client(_EvaluationService(self.complete_report)).post(
            "/api/v1/evaluate",
            files={
                "question_paper": ("questions.pdf", PDF_BYTES, "application/pdf"),
                "student_answer_sheet": ("student.pdf", PDF_BYTES, "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_INPUT")

    def test_missing_student_sheet_returns_safe_validation_error(self):
        response = self.client(_EvaluationService(self.complete_report)).post(
            "/api/v1/evaluate",
            files={
                "question_paper": ("questions.pdf", PDF_BYTES, "application/pdf"),
                "model_answer": ("answers.pdf", PDF_BYTES, "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_INPUT")

    def test_unsupported_file_type_is_rejected_after_content_validation(self):
        response = self.client(_EvaluationService(self.complete_report)).post(
            "/api/v1/evaluate",
            files=self.files(student_answer_sheet=("student.exe", b"MZ", "application/octet-stream")),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "UNSUPPORTED_FILE_TYPE")

    def test_oversized_file_is_rejected(self):
        settings = replace(self.settings, max_upload_size_mb=1)
        oversized_pdf = b"%PDF-1.4\n" + b"x" * (1024 * 1024)
        response = self.client(_EvaluationService(self.complete_report), settings).post(
            "/api/v1/evaluate",
            files=self.files(student_answer_sheet=("student.pdf", oversized_pdf, "application/pdf")),
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "FILE_TOO_LARGE")

    def test_successful_evaluation_returns_typed_report_and_cleans_temp_uploads(self):
        service = _EvaluationService(self.complete_report)
        response = self.client(service).post(
            "/api/v1/evaluate",
            files=self.files(),
            data={"student_id": "student-1", "subject": "AI"},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["evaluation_id"].startswith("evaluation_"))
        self.assertEqual(payload["status"], "complete")
        self.assertIn("summary", payload)
        self.assertIn("question_results", payload)
        self.assertIn("warnings", payload)
        self.assertEqual(len(service.requests), 1)
        self.assertFalse(service.requests[0].question_paper_path.parent.exists())

    def test_partially_evaluated_report_remains_a_successful_response(self):
        response = self.client(_EvaluationService(self.partial_report)).post("/api/v1/evaluate", files=self.files())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "partially_evaluated")
        self.assertTrue(response.json()["warnings"])

    def test_ocr_failure_is_translated_without_internal_details(self):
        report = EvaluationReportGenerator().failed_report("Student handwritten text extraction failed.")
        response = self.client(_EvaluationService(report)).post("/api/v1/evaluate", files=self.files())
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual(response.json()["error"]["code"], "OCR_FAILED")
        self.assertNotIn("Traceback", response.text)

    def test_internal_exception_has_controlled_response(self):
        response = self.client(_EvaluationService(error=RuntimeError("sensitive internal failure"))).post(
            "/api/v1/evaluate", files=self.files(),
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("sensitive internal failure", response.text)

    def test_duplicate_question_id_is_reported_as_question_parse_failure(self):
        problem = _failed_report_problem("Duplicate question ID: Q1", "evaluation-1")
        self.assertEqual((problem.status_code, problem.code), (422, "QUESTION_PARSE_FAILED"))
