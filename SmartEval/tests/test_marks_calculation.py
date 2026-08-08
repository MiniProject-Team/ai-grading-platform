import unittest

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.question import Question
from domain.entities.total_marks_result import TotalMarksResult
from domain.value_objects.question_id import QuestionId
from evaluation.marks.marks_calculator import WeightedMarksCalculator
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.scoring_config import ScoringWeights, WeightedScoringStrategy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator


def question(number=1, max_marks=10):
    return Question(QuestionId(number), number, f"Question {number}", max_marks)


def evaluation(number=1, semantic=1.0, concept=1.0, relevance=1.0, completeness=1.0, status="correct"):
    return EvaluationResult(QuestionId(number), semantic, concept, relevance, completeness, status, "test")


class _FixedStrategy:
    def __init__(self, score): self.score = score
    def calculate_score(self, result): return self.score, {}


class MarksCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.rounding = RoundingPolicy(1)
        self.calculator = WeightedMarksCalculator(WeightedScoringStrategy(ScoringWeights(.4, .3, .15, .15)), self.rounding)

    def test_perfect_answer_receives_maximum_marks(self):
        result = self.calculator.calculate(question(), evaluation())
        self.assertEqual(result.marks_awarded, 10.0)
        self.assertEqual(result.percentage, 100.0)

    def test_zero_scores_receive_zero_marks(self):
        result = self.calculator.calculate(question(), evaluation(semantic=0, concept=0, relevance=0, completeness=0, status="irrelevant"))
        self.assertEqual(result.marks_awarded, 0.0)

    def test_partial_answer_receives_proportional_marks(self):
        result = self.calculator.calculate(question(), evaluation(semantic=.55, concept=.55, relevance=.55, completeness=.55, status="partially_correct"))
        self.assertEqual(result.marks_awarded, 5.5)

    def test_weighted_formula_and_breakdown_are_transparent(self):
        result = self.calculator.calculate(question(), evaluation(semantic=.9, concept=.8, relevance=.95, completeness=.85, status="mostly_correct"))
        self.assertEqual(result.marks_awarded, 8.7)
        self.assertAlmostEqual(result.breakdown["semantic_similarity"].contribution, .36)
        self.assertAlmostEqual(result.breakdown["relevance"].contribution, .1425)

    def test_marks_are_bounded_to_valid_range(self):
        above = WeightedMarksCalculator(_FixedStrategy(1.2), self.rounding).calculate(question(), evaluation())
        below = WeightedMarksCalculator(_FixedStrategy(-.5), self.rounding).calculate(question(), evaluation())
        self.assertEqual(above.marks_awarded, 10.0)
        self.assertEqual(below.marks_awarded, 0.0)

    def test_no_answer_is_zero_and_missing_model_is_unevaluated(self):
        no_answer = self.calculator.calculate(question(), evaluation(semantic=0, concept=0, relevance=0, completeness=0, status="no_answer"))
        missing = self.calculator.calculate(question(2), evaluation(2, semantic=None, concept=None, relevance=None, completeness=None, status="model_answer_missing"))
        self.assertEqual(no_answer.marks_awarded, 0.0)
        self.assertIsNone(missing.marks_awarded)
        self.assertEqual(missing.evaluation_status, "model_answer_missing")

    def test_rounding_uses_half_up_policy(self):
        self.assertEqual(self.rounding.round_marks(8.46), 8.5)

    def test_rejects_invalid_weights_and_maximum_marks(self):
        with self.assertRaises(ValueError):
            ScoringWeights(.4, .3, .15, .10)
        with self.assertRaises(ValueError):
            question(max_marks=0)

    def test_total_uses_evaluated_maximum_not_exam_maximum_when_model_missing(self):
        marks = [
            self.calculator.calculate(question(1, 10), evaluation(1, semantic=.8, concept=.8, relevance=.8, completeness=.8)),
            self.calculator.calculate(question(2, 20), evaluation(2, semantic=.5, concept=.5, relevance=.5, completeness=.5, status="partially_correct")),
            self.calculator.calculate(question(3, 10), evaluation(3, semantic=None, concept=None, relevance=None, completeness=None, status="model_answer_missing")),
        ]
        total = TotalMarksCalculator(self.rounding).calculate(marks)
        self.assertEqual(total.awarded_marks, 18.0)
        self.assertEqual(total.evaluated_maximum_marks, 30)
        self.assertEqual(total.exam_maximum_marks, 40)
        self.assertEqual(total.percentage, 60.0)
        self.assertEqual(total.missing_model_answers, 1)
        self.assertEqual(total.unevaluated_questions, (QuestionId(3),))
