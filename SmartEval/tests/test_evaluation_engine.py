import unittest

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId
from evaluation.evaluation_engine import EvaluationEngine
from evaluation.thresholds import EvaluationThresholds


class _Semantic:
    def __init__(self, value): self.value = value
    def evaluate(self, model, student): return self.value


class _Concept:
    def __init__(self, value): self.value = value
    def evaluate(self, model, student): return self.value


class _Relevance:
    def __init__(self, value): self.value = value
    def evaluate(self, question, student): return self.value


def item(model_text="model answer", student_text="student answer"):
    identifier = QuestionId(1)
    return EvaluationItem(Question(identifier, 1, "question", 5), ModelAnswer(identifier, model_text) if model_text is not None else None, StudentAnswer(identifier, student_text))


class EvaluationEngineTests(unittest.TestCase):
    def engine(self, semantic=.9, concept=.85, relevance=.9, completeness=.85):
        return EvaluationEngine(_Semantic(semantic), _Concept(concept), _Relevance(relevance), _Concept(completeness), EvaluationThresholds(.8, .65, .4, .65, .4, .65))

    def test_correct_signal_result_contains_no_marks(self):
        result = self.engine().evaluate(item())
        self.assertEqual(result.status, "correct")
        self.assertEqual(result.semantic_similarity, .9)
        self.assertFalse(hasattr(result, "marks_awarded"))

    def test_partial_and_irrelevant_statuses(self):
        self.assertEqual(self.engine(.5, .5, .5, .5).evaluate(item()).status, "partially_correct")
        self.assertEqual(self.engine(.2, .2, .1, .2).evaluate(item()).status, "irrelevant")

    def test_empty_student_answer_skips_embedding_evaluation(self):
        result = self.engine().evaluate(item(student_text=""))
        self.assertEqual(result.status, "no_answer")
        self.assertEqual(result.semantic_similarity, 0.0)

    def test_missing_model_answer_returns_explicit_state(self):
        result = self.engine().evaluate(item(model_text=None))
        self.assertEqual(result.status, "model_answer_missing")
        self.assertIsNone(result.semantic_similarity)
