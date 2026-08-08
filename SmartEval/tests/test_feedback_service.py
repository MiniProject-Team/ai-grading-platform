import unittest

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.marks_result import MarksResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId
from feedback.feedback_config import FeedbackConfig
from feedback.feedback_service import FeedbackService
from feedback.rule_based_feedback import RuleBasedFeedbackGenerator


def item(number: int) -> EvaluationItem:
    identifier = QuestionId(number)
    return EvaluationItem(
        Question(identifier, number, f"Question {number}", 5),
        ModelAnswer(identifier, "Expected answer."),
        StudentAnswer(identifier, "Student answer."),
    )


class FeedbackServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = FeedbackService(RuleBasedFeedbackGenerator(FeedbackConfig(.9, .7, .4, .1, .75, .5)))

    def test_keeps_feedback_with_its_question(self):
        first, second = item(1), item(2)
        evaluations = [
            EvaluationResult(QuestionId(1), .9, .9, .9, .9, "correct", "test"),
            EvaluationResult(QuestionId(2), .5, .4, .5, .4, "partially_correct", "test"),
        ]
        marks = [
            MarksResult(QuestionId(1), 5, 4.5, 90.0, "correct"),
            MarksResult(QuestionId(2), 5, 2.0, 40.0, "partially_correct"),
        ]

        results = self.service.generate([first, second], evaluations, marks)

        self.assertEqual([result.question_id for result in results], [QuestionId(1), QuestionId(2)])
        self.assertEqual(results[1].marks_awarded, 2.0)

    def test_rejects_missing_mapped_result(self):
        mapped = item(1)
        with self.assertRaisesRegex(ValueError, "one evaluation"):
            self.service.generate([mapped], [], [])
