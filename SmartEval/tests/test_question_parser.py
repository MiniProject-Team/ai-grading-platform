import unittest

from parsers.question_parser import QuestionParser


class QuestionParserTests(unittest.TestCase):
    def test_parses_common_ids_and_marks(self):
        questions = QuestionParser().parse("Q1. Define AI. (5 Marks)\n\nQuestion 2 Explain ML. [10]\n\n3) Define DL. 2 Marks")
        self.assertEqual([str(question.question_id) for question in questions], ["Q1", "Q2", "Q3"])
        self.assertEqual([question.max_marks for question in questions], [5, 10, 2])

    def test_keeps_unavailable_marks_as_none(self):
        question = QuestionParser().parse("Q1. Define AI.")[0]
        self.assertIsNone(question.max_marks)

    def test_rejects_duplicate_question_ids(self):
        with self.assertRaises(ValueError):
            QuestionParser().parse("Q1. First question\nQ1. Duplicate question")

    def test_rejects_invalid_marks(self):
        with self.assertRaises(ValueError):
            QuestionParser().parse("Q1. Invalid marks. (0 Marks)")
