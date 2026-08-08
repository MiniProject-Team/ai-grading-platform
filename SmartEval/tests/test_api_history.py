from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from api.app import create_app
from config.settings import Settings
from domain.entities.evaluation_report import ExamInformation, StudentInformation
from integration.evaluation_service import EndToEndEvaluationResult
from persistence.base import Base
from persistence.database import create_database_engine
from tests.report_fixtures import build_report


PDF_BYTES = b"%PDF-1.4\nmock upload\n"


class _EvaluationService:
    def evaluate_and_export(self, request):
        report = replace(
            build_report(),
            report_id=request.report_id or "missing",
            student_information=StudentInformation(request.student_id, request.student_name, request.roll_number),
            exam_information=ExamInformation(
                request.exam_name, request.subject, request.semester, request.exam_date, 5, request.exam_id,
            ),
        )
        return EndToEndEvaluationResult(report, None, Path("report.json"), Path("report.txt"))


class APIHistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        root = Path(self.directory.name)
        self.settings = Settings(
            log_directory=root / "logs",
            output_directory=root / "outputs",
            temp_directory=root / "temp",
            database_url=f"sqlite+pysqlite:///{root / 'history.db'}",
        )
        engine = create_database_engine(self.settings.database_url)
        Base.metadata.create_all(engine)
        engine.dispose()
        self.client = TestClient(create_app(self.settings, evaluation_service_factory=_EvaluationService))

    def tearDown(self):
        self.client.app.state.database_engine.dispose()
        self.directory.cleanup()

    @staticmethod
    def files():
        return {
            "question_paper": ("questions.pdf", PDF_BYTES, "application/pdf"),
            "model_answer": ("answers.pdf", PDF_BYTES, "application/pdf"),
            "student_answer_sheet": ("student.pdf", PDF_BYTES, "application/pdf"),
        }

    def test_persisted_evaluation_can_be_retrieved_and_listed(self):
        response = self.client.post(
            "/api/v1/evaluate",
            files=self.files(),
            data={"student_id": "student-1", "student_name": "Ada", "exam_id": "exam-1", "exam_name": "AI Midterm"},
            headers={"Idempotency-Key": "retry-key-1"},
        )
        self.assertEqual(response.status_code, 200)
        evaluation_id = response.json()["evaluation_id"]
        self.assertEqual(self.client.get(f"/api/v1/evaluations/{evaluation_id}").status_code, 200)

        listing = self.client.get("/api/v1/evaluations", params={"student_id": "student-1"})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["total"], 1)
        self.assertEqual(listing.json()["items"][0]["evaluation_id"], evaluation_id)
        self.assertEqual(self.client.get("/api/v1/students/student-1/evaluations").json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/exams/exam-1/evaluations").json()["total"], 1)

    def test_idempotency_key_prevents_duplicate_history_rows(self):
        headers = {"Idempotency-Key": "retry-key-2"}
        first = self.client.post("/api/v1/evaluate", files=self.files(), headers=headers)
        second = self.client.post("/api/v1/evaluate", files=self.files(), headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["evaluation_id"], second.json()["evaluation_id"])
        self.assertEqual(self.client.get("/api/v1/evaluations").json()["total"], 1)
