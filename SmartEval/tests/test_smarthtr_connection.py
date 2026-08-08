from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from parsers.student_answer_parser import StudentAnswerParser
from services.student_text_provider import SmartHTRLocalOutputProvider


class SmartHTRConnectionTests(unittest.TestCase):
    def test_reads_smarthtr_style_page_text_directory_in_order(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "page_002.txt").write_text("Q2. Second answer", encoding="utf-8")
            (output / "page_001.txt").write_text("Q1. First answer", encoding="utf-8")
            text = SmartHTRLocalOutputProvider().get_text(output)
        self.assertEqual(text, "Q1. First answer\n\nQ2. Second answer")

    def test_reports_unstructured_ocr_text_without_guessing_boundaries(self):
        with self.assertRaisesRegex(ValueError, "No numbered student answers"):
            StudentAnswerParser().parse("OCR text without a detected question identifier")
