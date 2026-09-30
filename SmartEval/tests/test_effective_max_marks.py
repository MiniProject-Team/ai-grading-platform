from pathlib import Path
import unittest

from domain.entities.marks_result import MarksResult
from evaluation.marks.effective_max_marks import calculate_effective_max_marks
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from parsers.question_parser import QuestionParser
from parsers.model_answer_parser import ModelAnswerParser
from services.input_manager import InputManager


class EffectiveMaximumTests(unittest.TestCase):
    def test_required_maximum_cases(self):
        cases = [
            ("Q1. First [7]\nOR\nQ2. Second [6]", 7),
            ("Q1. First [7]\nOR\nQ2. Second [6]\nQ3. Third [8]\nOR\nQ4. Fourth [7]", 15),
            ("Q1. First [7]\nOR\nQ2. Second [7]", 7),
            ("Q9. Compulsory [5]\nQ2. First [7]\nOR\nQ6. Second [6]", 12),
            ("Q1(a) First [2]\nb) Second [3]\nc) Third [2]\nOR\nQ2(a) Fourth [4]\nb) Fifth [2]", 7),
            ("Q1. First [5]\nQ2. Second [5]\nQ3. Third [10]", 20),
            ("Q1(a) First [3]\nb) Second [4]\nOR\nQ2(a) Third [3]\nb) Fourth [3]", 7),
        ]
        for paper, expected in cases:
            with self.subTest(paper=paper):
                self.assertEqual(calculate_effective_max_marks(QuestionParser().parse(paper)), expected)

    def test_percentage_uses_whole_paper_even_if_alternative_unevaluated(self):
        questions = QuestionParser().parse(
            "Q1. First [7]\nOR\nQ2. Second [6]\nQ3. Third [8]\nOR\nQ4. Fourth [7]"
        )
        marks = [MarksResult(q.question_id, q.max_marks, awarded, None, status)
                 for q, awarded, status in zip(questions, [4.9, None, 5.6, 0],
                                              ['partially_correct', 'model_answer_missing', 'partially_correct', 'no_answer'])]
        total = TotalMarksCalculator(RoundingPolicy(1)).calculate(marks, questions)
        self.assertEqual(total.awarded_marks, 10.5)
        self.assertEqual(total.exam_maximum_marks, 15)
        self.assertEqual(total.percentage, 70.0)

    def test_zero_denominator(self):
        total = TotalMarksCalculator(RoundingPolicy(1)).calculate([])
        self.assertEqual(total.exam_maximum_marks, 0)
        self.assertIsNone(total.percentage)

    def test_duplicate_ids_are_rejected(self):
        questions = QuestionParser().parse('Q1. First [7]')
        with self.assertRaisesRegex(ValueError, 'Duplicate question ID'):
            calculate_effective_max_marks(questions * 2)

    def test_real_teacher_input_pipeline(self):
        root = Path(__file__).resolve().parents[1]
        paper, model = InputManager().load_teacher_inputs(
            root / 'tests/fixtures/or_question_paper.txt', root / 'inputs/model_answer_fixture.txt'
        )
        questions = QuestionParser().parse(paper)
        models = ModelAnswerParser().parse(model)
        self.assertTrue(models)
        self.assertEqual([q.max_marks for q in questions], [4, 3, 4, 3, 4, 4, 4, 4])
        self.assertEqual(sum(q.max_marks for q in questions), 30)
        self.assertEqual(calculate_effective_max_marks(questions), 15)

    def test_original_pdf_extracted_marks_columns(self):
        text = (Path(__file__).parent / 'fixtures/or_question_paper_pdf_text.txt').read_text(encoding='utf-8')
        questions = QuestionParser().parse(text)
        self.assertEqual([q.max_marks for q in questions], [4, 3, 4, 3, 4, 4, 4, 4])
        self.assertEqual(calculate_effective_max_marks(questions), 15)

    def test_bare_numbers_without_marks_table_are_not_inferred(self):
        questions = QuestionParser().parse('Q1. Explain\n4\n703.1')
        self.assertIsNone(questions[0].max_marks)


if __name__ == '__main__':
    unittest.main()
