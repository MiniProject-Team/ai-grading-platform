from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.input_pipeline import InputPipeline
from config.settings import Settings
from services.input_manager import InputManager


class InputPipelineTests(unittest.TestCase):
    def test_complete_phase_four_flow(self):
        analysis = InputPipeline(Settings.from_environment()).run(
            Path("inputs/question_paper_fixture.txt"),
            Path("inputs/model_answer_fixture.txt"),
            Path("inputs/student_text_fixture.txt"),
        )
        self.assertEqual([str(question.question_id) for question in analysis.questions], ["Q1", "Q2", "Q3"])
        self.assertEqual([str(answer.question_id) for answer in analysis.model_answers], ["Q1", "Q2", "Q3"])
        self.assertEqual([str(answer.question_id) for answer in analysis.student_answers], ["Q1", "Q2", "Q3"])
        self.assertTrue(all(not item.model_answer_missing and not item.student_answer_missing for item in analysis.items))

    def test_rejects_invalid_question_paper_before_requesting_student_ocr(self):
        class StudentProvider:
            calls = 0

            def get_text(self, source):
                self.calls += 1
                raise AssertionError("Student OCR should not run for an invalid question paper")

        with TemporaryDirectory() as directory:
            root = Path(directory)
            question_paper = root / "questions.txt"
            model_answer = root / "answers.txt"
            question_paper.write_text("Q1. First question\nQ1. Duplicate question", encoding="utf-8")
            model_answer.write_text("Q1. Model answer", encoding="utf-8")
            provider = StudentProvider()
            pipeline = InputPipeline(
                Settings(log_directory=root / "logs"),
                input_manager=InputManager(student_provider=provider),
            )
            with self.assertRaisesRegex(ValueError, "Duplicate question ID: Q1"):
                pipeline.run(question_paper, model_answer, root / "student.pdf")

        self.assertEqual(provider.calls, 0)
