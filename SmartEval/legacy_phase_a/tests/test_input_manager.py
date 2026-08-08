from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from smarteval.core.exceptions import InputValidationError
from smarteval.inputs.input_manager import InputManager


class InputManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.manager = InputManager()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_all_required_inputs(self) -> None:
        inputs = self.manager.load(
            self._write("questions.txt", "Q1. Define AI."),
            self._write("model.txt", "AI is machine intelligence."),
            self._write("student.txt", "AI means machines can learn."),
        )
        self.assertEqual(inputs.question_paper.text, "Q1. Define AI.")
        self.assertIn("machine", inputs.model_answer.text)
        self.assertEqual(inputs.student_ocr.kind.value, "student_ocr")

    def test_loads_smarthtr_page_text_directory_in_order(self) -> None:
        pages = self.root / "ocr"
        pages.mkdir()
        (pages / "page_002.txt").write_text("second", encoding="utf-8")
        (pages / "page_001.txt").write_text("first", encoding="utf-8")
        inputs = self.manager.load(
            self._write("questions.txt", "questions"),
            self._write("model.txt", "model"),
            pages,
        )
        self.assertEqual(inputs.student_ocr.text, "first\n\nsecond")

    def test_loads_json_text_field(self) -> None:
        questions = self._write("questions.txt", "questions")
        model = self.root / "model.json"
        model.write_text(json.dumps({"text": "model answer"}), encoding="utf-8")
        inputs = self.manager.load(questions, model, self._write("student.txt", "student"))
        self.assertEqual(inputs.model_answer.text, "model answer")

    def test_rejects_empty_input(self) -> None:
        with self.assertRaises(InputValidationError):
            self.manager.load(
                self._write("questions.txt", ""),
                self._write("model.txt", "model"),
                self._write("student.txt", "student"),
            )
