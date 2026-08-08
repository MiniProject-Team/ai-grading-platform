from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config.settings import Settings
from domain.entities.evaluation_report import ExamInformation, StudentInformation
from persistence.base import Base
from persistence.database import create_database_engine, create_session_factory
from persistence.models import EvaluationRecord, StudentRecord
from persistence.service import EvaluationPersistenceService, PersistenceError
from reporting.evaluation_report_generator import EvaluationReportGenerator
from tests.report_fixtures import build_report


class EvaluationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        root = Path(self.directory.name)
        self.settings = Settings(
            log_directory=root / "logs",
            output_directory=root / "outputs",
            database_url=f"sqlite+pysqlite:///{root / 'history.db'}",
        )
        self.engine = create_database_engine(self.settings.database_url)
        Base.metadata.create_all(self.engine)
        self.service = EvaluationPersistenceService(create_session_factory(self.engine), self.settings)
        self.report = replace(
            build_report(),
            report_id="evaluation_persistence_test",
            student_information=StudentInformation("student-1", "Ada Student", "R-1"),
            exam_information=ExamInformation("Midterm", "AI", "Semester 1", "2026-08-08", 5, "exam-ai-1"),
        )

    def tearDown(self):
        self.engine.dispose()
        self.directory.cleanup()

    def test_persists_normalized_records_and_immutable_snapshot(self):
        stored = self.service.persist(
            self.report,
            question_paper_filename="questions.pdf",
            model_answer_filename="model.pdf",
            student_answer_filename="student.pdf",
        )
        self.assertEqual(stored.evaluation_id, self.report.report_id)
        self.assertEqual(stored.report_payload["summary"], self.report.to_dict()["summary"])

        session = create_session_factory(self.engine)()
        try:
            evaluation = session.scalar(select(EvaluationRecord).where(EvaluationRecord.evaluation_id == self.report.report_id))
            self.assertIsNotNone(evaluation)
            assert evaluation is not None
            self.assertEqual(evaluation.student_answer_filename, "student.pdf")
            self.assertEqual(len(evaluation.questions), 5)
            self.assertEqual(evaluation.questions[0].semantic_similarity, 0.95)
            self.assertTrue(evaluation.questions[0].strengths)
            self.assertEqual(session.scalar(select(StudentRecord).where(StudentRecord.student_id == "student-1")).name, "Ada Student")
        finally:
            session.close()

    def test_duplicate_evaluation_id_is_idempotent(self):
        first = self.service.persist(self.report)
        second = self.service.persist(self.report)
        self.assertEqual(first.evaluation_id, second.evaluation_id)
        session = create_session_factory(self.engine)()
        try:
            self.assertEqual(len(list(session.scalars(select(EvaluationRecord)))), 1)
        finally:
            session.close()

    def test_list_filters_by_student_exam_and_status(self):
        self.service.persist(self.report)
        alternate = replace(
            self.report,
            report_id="evaluation_persistence_test_2",
            student_information=StudentInformation("student-2", "Grace Student"),
        )
        self.service.persist(alternate)
        student_page = self.service.list(page=1, page_size=10, student_id="student-1")
        exam_page = self.service.list(page=1, page_size=10, exam_id="exam-ai-1", status="partially_evaluated")
        self.assertEqual(student_page.total, 1)
        self.assertEqual(student_page.items[0].evaluation_id, self.report.report_id)
        self.assertEqual(exam_page.total, 2)

    def test_retention_setting_omits_normalized_answer_content(self):
        service = EvaluationPersistenceService(
            create_session_factory(self.engine), replace(self.settings, retain_evaluation_content=False),
        )
        service.persist(self.report)
        session = create_session_factory(self.engine)()
        try:
            evaluation = session.scalar(select(EvaluationRecord).where(EvaluationRecord.evaluation_id == self.report.report_id))
            assert evaluation is not None
            self.assertIsNone(evaluation.questions[0].student_answer)
            self.assertIsNone(evaluation.questions[0].model_answer)
            snapshot = service.get(self.report.report_id)
            assert snapshot is not None
            self.assertEqual(snapshot.report_payload["question_results"][0]["student_answer"], "")
            self.assertIsNone(snapshot.report_payload["question_results"][0]["model_answer"])
        finally:
            session.close()

    def test_database_error_rolls_back_transaction(self):
        with patch(
            "persistence.service.SQLAlchemyEvaluationQuestionRepository.add_all",
            side_effect=SQLAlchemyError("forced write failure"),
        ):
            with self.assertRaises(PersistenceError):
                self.service.persist(self.report)
        self.assertIsNone(self.service.get(self.report.report_id))

    def test_failed_report_is_stored_with_safe_error_summary(self):
        report = EvaluationReportGenerator().failed_report(
            "Student handwritten text extraction failed.",
            report_id="evaluation_failed_test",
        )
        self.service.persist(report)
        stored = self.service.get(report.report_id)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.status, "failed")
        session = create_session_factory(self.engine)()
        try:
            evaluation = session.scalar(select(EvaluationRecord).where(EvaluationRecord.evaluation_id == report.report_id))
            assert evaluation is not None
            self.assertEqual(evaluation.error_summary, "Student handwritten text extraction failed.")
        finally:
            session.close()
