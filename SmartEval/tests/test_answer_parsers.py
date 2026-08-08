import unittest

from parsers.model_answer_parser import ModelAnswerParser
from parsers.student_answer_parser import StudentAnswerParser


class AnswerParserTests(unittest.TestCase):
    def test_parses_model_answers(self):
        answers = ModelAnswerParser().parse("Q1.\nFirst model answer\n\nAnswer 2\nSecond model answer")
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])
        self.assertEqual(answers[1].answer_text, "Second model answer")

    def test_segments_complete_student_answers(self):
        answers = StudentAnswerParser().parse("Question 1\nFirst complete answer\nwith another line\n\nQ2.\nSecond complete answer")
        self.assertEqual(answers[0].answer_text, "First complete answer\nwith another line")
        self.assertEqual(answers[1].answer_text, "Second complete answer")
