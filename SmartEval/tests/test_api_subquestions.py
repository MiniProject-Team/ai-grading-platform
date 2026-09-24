from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import fitz
from fastapi.testclient import TestClient

from api.app import create_app
from config.settings import Settings
from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult
from integration.evaluation_service import EvaluationService
from integration.ocr_service import OCRPageResult, OCRResult
from integration.student_text_provider import SmartHTRIntegrationService, SmartHTRStudentTextProvider
from persistence.service import PersistedEvaluation


QUESTION_TEXT = """Q.1 (a) First question [4]
b) Second question [3]
OR
Q.2 (a) Third question [4]
b) Fourth question [3]
Q.3 (a) Fifth question [4]
b) Sixth question [4]
OR
Q.4 (a) Seventh question [4]
b) Eighth question [4]
"""
MODEL_TEXT = """Q.1 (a) First model answer
Q.1 (b) Second model answer
Q.2 (a) Third model answer
Q.2 (b) Fourth model answer
Q.3 (a) Fifth model answer
Q.3 (b) Sixth model answer
Q.4 (a) Seventh model answer
Q.4 (b) Eighth model answer
"""
STUDENT_TEXT = "\n".join(
    f"Q{number}({subpart})\nStudent answer {number}{subpart}"
    for number in range(1, 5)
    for subpart in ("a", "b")
)


def _pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page(width=600, height=800)
    page.insert_textbox(fitz.Rect(20, 20, 580, 780), text, fontsize=8)
    content = document.tobytes()
    document.close()
    return content


class _OCRClient:
    def recognize(self, path: Path) -> OCRResult:
        return OCRResult(
            provider="test",
            extracted_text=STUDENT_TEXT,
            pages_processed=1,
            success=True,
            status="success",
            pages=(OCRPageResult(1, STUDENT_TEXT),),
        )


class _EvaluationEngine:
    def evaluate(self, item: EvaluationItem) -> EvaluationResult:
        return EvaluationResult(
            item.question.question_id,
            0.8,
            0.8,
            0.8,
            0.8,
            "correct",
            "test",
        )


class _Persistence:
    def persist(self, report, **kwargs):
        return PersistedEvaluation(report.report_id, report.status, report.to_dict())


class APISubquestionTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        root = Path(self.directory.name)
        settings = Settings(
            log_directory=root / "logs",
            output_directory=root / "outputs",
            temp_directory=root / "temp",
            database_url=None,
        )
        provider = SmartHTRStudentTextProvider(SmartHTRIntegrationService(_OCRClient()))
        service = EvaluationService(settings, student_text_provider=provider, evaluation_engine=_EvaluationEngine())
        self.client = TestClient(create_app(
            settings,
            evaluation_service_factory=lambda: service,
            persistence_service_factory=lambda: _Persistence(),
        ))

    def tearDown(self):
        self.directory.cleanup()

    def test_api_returns_independent_subquestion_results_and_metadata(self):
        response = self.client.post(
            "/api/v1/evaluate",
            files={
                "question_paper": ("questions.pdf", _pdf_bytes(QUESTION_TEXT), "application/pdf"),
                "model_answer": ("model.pdf", _pdf_bytes(MODEL_TEXT), "application/pdf"),
                "student_answer_sheet": ("student.pdf", _pdf_bytes("placeholder"), "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        results = payload["question_results"]
        expected_ids = [
            "Q1(a)", "Q1(b)", "Q2(a)", "Q2(b)",
            "Q3(a)", "Q3(b)", "Q4(a)", "Q4(b)",
        ]
        self.assertEqual(payload["summary"]["total_questions"], 8)
        self.assertEqual([result["question_id"] for result in results], expected_ids)
        self.assertEqual([result["max_marks"] for result in results], [4, 3, 4, 3, 4, 4, 4, 4])
        self.assertTrue(all(result["max_marks"] is not None and result["max_marks"] > 0 for result in results))
        self.assertEqual([result["alternative_group"] for result in results], [
            "OR_1", "OR_1", "OR_1", "OR_1", "OR_2", "OR_2", "OR_2", "OR_2",
        ])
        self.assertTrue(all(result["model_answer"] for result in results))
        self.assertNotIn("Q1", expected_ids)
        self.assertNotIn("Q2", expected_ids)
        self.assertNotIn("Second question", results[0]["question"])
        self.assertNotIn("First question", results[1]["question"])


if __name__ == "__main__":
    unittest.main()
