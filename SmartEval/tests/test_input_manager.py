from pathlib import Path
import unittest

from services.input_manager import InputManager


class InputManagerTests(unittest.TestCase):
    def test_loads_three_fixture_documents(self):
        inputs = InputManager().load(
            Path("inputs/question_paper_fixture.txt"),
            Path("inputs/model_answer_fixture.txt"),
            Path("inputs/student_text_fixture.txt"),
        )
        self.assertIn("Artificial Intelligence", inputs.question_paper_text)
        self.assertIn("Machine Learning", inputs.model_answer_text)
        self.assertIn("neural networks", inputs.student_text)
