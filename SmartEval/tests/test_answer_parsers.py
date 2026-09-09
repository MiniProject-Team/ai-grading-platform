import unittest

from parsers.model_answer_parser import ModelAnswerParser
from parsers.student_answer_parser import StudentAnswerParser
from domain.value_objects.question_id import QuestionId


class AnswerParserTests(unittest.TestCase):
    def test_parses_model_answers(self):
        answers = ModelAnswerParser().parse("Q1.\nFirst model answer\n\nAnswer 2\nSecond model answer")
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])
        self.assertEqual(answers[1].answer_text, "Second model answer")

    def test_segments_complete_student_answers(self):
        answers = StudentAnswerParser().parse("Question 1\nFirst complete answer\nwith another line\n\nQ2.\nSecond complete answer")
        self.assertEqual(answers[0].answer_text, "First complete answer\nwith another line")
        self.assertEqual(answers[1].answer_text, "Second complete answer")

    def test_accepts_common_ocr_answer_heading_variants(self):
        answers = StudentAnswerParser().parse("Ans 1: First answer\nAnswer No. 2 Second answer")
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])

    def test_uses_low_confidence_sequential_fallback_when_headings_are_absent(self):
        answers = StudentAnswerParser().parse("First answer\n\nSecond answer", [QuestionId(1), QuestionId(2)])
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])
        self.assertTrue(all(answer.mapping_method == "sequential_fallback" for answer in answers))
