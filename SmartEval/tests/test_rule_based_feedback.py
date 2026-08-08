import unittest

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.marks_result import MarksResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId
from feedback.feedback_config import FeedbackConfig
from feedback.rule_based_feedback import RuleBasedFeedbackGenerator


def config() -> FeedbackConfig:
    return FeedbackConfig(.9, .7, .4, .1, .75, .5)


def inputs(
    *,
    semantic=.9,
    coverage=.9,
    relevance=.9,
    completeness=.9,
    status="correct",
    marks=9.0,
    model=True,
    student="student answer",
):
    identifier = QuestionId(1)
    question = Question(identifier, 1, "Explain machine learning", 10)
    model_answer = ModelAnswer(identifier, "Machine learning learns patterns from data.") if model else None
    student_answer = StudentAnswer(identifier, student)
    evaluation = EvaluationResult(identifier, semantic, coverage, relevance, completeness, status, "test")
    marks_result = MarksResult(identifier, 10, marks, None if marks is None else marks * 10, status)
    return question, model_answer, student_answer, evaluation, marks_result


class RuleBasedFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.generator = RuleBasedFeedbackGenerator(config())

    def generate(self, **kwargs):
        return self.generator.generate(*inputs(**kwargs))

    def test_perfect_answer_receives_positive_feedback(self):
        result = self.generate(marks=10.0)
        self.assertEqual(result.status, "correct")
        self.assertTrue(result.strengths)
        self.assertFalse(result.missing_concepts)
        self.assertIn("accurate", result.overall_feedback)

    def test_mostly_correct_answer_has_strength_and_suggestion(self):
        result = self.generate(semantic=.7, coverage=.7, relevance=.7, completeness=.7, status="mostly_correct", marks=7.0)
        self.assertTrue(result.strengths)
        self.assertTrue(result.improvement_suggestions)

    def test_partially_correct_answer_reports_supported_missing_coverage(self):
        result = self.generate(semantic=.45, coverage=.2, relevance=.45, completeness=.45, status="partially_correct", marks=4.0)
        self.assertTrue(result.missing_concepts)
        self.assertTrue(result.improvement_suggestions)

    def test_irrelevant_answer_mentions_relevance(self):
        result = self.generate(semantic=.2, coverage=.2, relevance=.1, completeness=.2, status="irrelevant", marks=1.0)
        self.assertTrue(any("focus" in area for area in result.weak_areas))
        self.assertIn("focus", result.overall_feedback)

    def test_empty_answer_returns_no_answer_message_without_semantic_feedback(self):
        result = self.generate(semantic=0, coverage=0, relevance=0, completeness=0, status="no_answer", marks=0.0, student="")
        self.assertEqual(result.overall_feedback, "No answer was detected for this question.")
        self.assertFalse(result.strengths)
        self.assertFalse(result.weak_areas)

    def test_missing_model_answer_returns_unavailable_message(self):
        result = self.generate(semantic=None, coverage=None, relevance=None, completeness=None, status="model_answer_missing", marks=None, model=False)
        self.assertEqual(result.overall_feedback, "Evaluation could not be completed because the model answer is unavailable.")
        self.assertFalse(result.missing_concepts)

    def test_high_coverage_but_low_completeness_identifies_incomplete_explanation(self):
        result = self.generate(semantic=.8, coverage=.9, relevance=.8, completeness=.2, status="mostly_correct", marks=7.0)
        self.assertTrue(any("supporting details" in area for area in result.weak_areas))
        self.assertFalse(result.missing_concepts)

    def test_high_relevance_but_low_semantic_similarity_reflects_both_metrics(self):
        result = self.generate(semantic=.2, coverage=.8, relevance=.9, completeness=.8, status="mostly_correct", marks=7.0)
        self.assertTrue(any("directly addresses" in strength for strength in result.strengths))
        self.assertTrue(any("differs substantially" in area for area in result.weak_areas))

    def test_all_metrics_high_is_mostly_positive(self):
        result = self.generate(semantic=.95, coverage=.95, relevance=.95, completeness=.95, marks=9.5)
        self.assertGreaterEqual(len(result.strengths), 2)
        self.assertFalse(result.weak_areas)

    def test_all_metrics_low_produces_clear_improvements(self):
        result = self.generate(semantic=.1, coverage=.1, relevance=.1, completeness=.1, status="irrelevant", marks=0.0)
        self.assertTrue(result.weak_areas)
        self.assertTrue(result.improvement_suggestions)

    def test_missing_required_result_is_a_clear_error(self):
        question, model_answer, student_answer, evaluation, _ = inputs()
        with self.assertRaisesRegex(ValueError, "MarksResult"):
            self.generator.generate(question, model_answer, student_answer, evaluation, None)


class FeedbackConfigurationTests(unittest.TestCase):
    def test_rejects_invalid_score_threshold_order(self):
        with self.assertRaises(ValueError):
            FeedbackConfig(.7, .9, .4, .1, .75, .5)
