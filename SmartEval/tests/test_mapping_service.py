import unittest

from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId
from services.answer_mapping_service import AnswerMappingService


class AnswerMappingServiceTests(unittest.TestCase):
    def setUp(self):
        self.questions = [Question(QuestionId(1), 1, "Question one", 5), Question(QuestionId(2), 2, "Question two", 10)]

    def test_marks_missing_model_answer_without_creating_score(self):
        items = AnswerMappingService().map(self.questions, [ModelAnswer(QuestionId(1), "model")], [StudentAnswer(QuestionId(1), "student")])
        self.assertFalse(items[0].model_answer_missing)
        self.assertTrue(items[1].model_answer_missing)
        self.assertIsNone(items[1].model_answer)

    def test_creates_empty_student_answer_when_missing(self):
        items = AnswerMappingService().map(self.questions, [ModelAnswer(QuestionId(1), "model"), ModelAnswer(QuestionId(2), "model")], [StudentAnswer(QuestionId(1), "student")])
        self.assertTrue(items[1].student_answer_missing)
        self.assertEqual(items[1].student_answer.answer_text, "")
