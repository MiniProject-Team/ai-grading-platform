from pathlib import Path
import unittest

from app.input_pipeline import InputAnalysis
from app.marks_pipeline import MarksPipeline
from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.value_objects.question_id import QuestionId
from evaluation.marks.marks_calculator import WeightedMarksCalculator
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.scoring_config import ScoringWeights, WeightedScoringStrategy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator


class _EvaluationPipeline:
    def run(self, question_paper, model_answer, student_text):
        identifier = QuestionId(1)
        question = Question(identifier, 1, "Define AI", 10)
        item = EvaluationItem(question, ModelAnswer(identifier, "model"), StudentAnswer(identifier, "student"))
        analysis = InputAnalysis([question], [item.model_answer], [item.student_answer], [item])
        result = EvaluationResult(identifier, .8, .8, .8, .8, "mostly_correct", "test")
        return analysis, [result]


class MarksPipelineTests(unittest.TestCase):
    def test_converts_evaluation_results_to_question_and_total_marks(self):
        rounding = RoundingPolicy(1)
        calculator = WeightedMarksCalculator(WeightedScoringStrategy(ScoringWeights(.4, .3, .15, .15)), rounding)
        pipeline = MarksPipeline(_EvaluationPipeline(), calculator, TotalMarksCalculator(rounding))

        analysis, marks, total = pipeline.run(Path("questions.txt"), Path("model.txt"), Path("student.txt"))

        self.assertEqual(len(analysis.items), 1)
        self.assertEqual(marks[0].marks_awarded, 8.0)
        self.assertEqual(total.awarded_marks, 8.0)
        self.assertEqual(total.percentage, 80.0)
