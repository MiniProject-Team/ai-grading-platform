from dataclasses import replace
import json
from pathlib import Path
import unittest

from domain.entities.marks_result import MarksResult, ScoreContribution
from domain.entities.question import Question
from domain.value_objects.question_id import QuestionId
from evaluation.marks.effective_earned_marks import calculate_effective_earned_marks
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from evaluation.marks.rounding import RoundingPolicy


def rows(specs):
    questions, marks = [], []
    for number, part, group, earned, maximum in specs:
        identifier = QuestionId(number, part)
        questions.append(Question(identifier, number, 'Question', maximum, alternative_group=group))
        marks.append(MarksResult(identifier, maximum, earned, None, 'no_answer' if earned == 0 else 'partially_correct'))
    return questions, marks


class EffectiveEarnedTests(unittest.TestCase):
    def test_required_cases(self):
        for earned, groups, expected in [
            ([5.4, 5.6], ['A', 'A'], 5.6),
            ([6, 5.7], ['B', 'B'], 6),
            ([5.4, 5.6, 6, 5.7], ['A', 'A', 'B', 'B'], 11.6),
            ([5, 0], ['A', 'A'], 5),
            ([4, 5, 3], [None, 'A', 'A'], 9),
            ([3, 4, 5], [None]*3, 12),
        ]:
            with self.subTest(earned=earned):
                q, m = rows([(i+1, None, group, value, 8) for i, (value, group) in enumerate(zip(earned, groups))])
                self.assertAlmostEqual(calculate_effective_earned_marks(m, q).earned, expected)

    def test_whole_alternatives_and_results_preserved(self):
        q, m = rows([(1,'a','A',3.2,4),(1,'b','A',2.2,3),(2,'a','A',3.3,4),(2,'b','A',2.3,3)])
        original = list(m)
        result = calculate_effective_earned_marks(m, q)
        self.assertAlmostEqual(result.earned, 5.6)
        self.assertEqual(result.or_groups['A']['selected_alternative'], 'Q2')
        self.assertEqual(m, original)
        self.assertEqual(len(m), 4)

    def test_partial_answer_and_missing_model_contribute_no_invented_marks(self):
        q, m = rows([(1,'a','A',3,4),(1,'b','A',0,3),(2,'a','A',2,4),(2,'b','A',2,3)])
        self.assertEqual(calculate_effective_earned_marks(m, q).earned, 4)
        m[3] = replace(m[3], marks_awarded=None, evaluation_status='model_answer_missing')
        self.assertEqual(calculate_effective_earned_marks(m, q).earned, 3)

    def test_cannot_mix_best_subquestions_from_different_sides(self):
        q,m=rows([(1,'a','A',4,4),(1,'b','A',0,3),(2,'a','A',1,4),(2,'b','A',3,3)])
        result=calculate_effective_earned_marks(m,q)
        self.assertEqual(result.earned,4)
        self.assertEqual(result.or_groups['A']['selected_alternative'],'Q1')

    def test_three_alternatives_and_maximum_are_independent(self):
        q,m=rows([(7,None,'A',4,10),(3,None,'A',5,6),(9,None,'A',3,7)])
        total=TotalMarksCalculator(RoundingPolicy(1)).calculate(m,q)
        self.assertEqual(total.awarded_marks,5)
        self.assertEqual(total.exam_maximum_marks,10)
        self.assertEqual(total.or_groups['A']['selected_alternative'],'Q3')

    def test_compulsory_marks_retain_existing_rounding(self):
        q,m=rows([(1,None,None,3.2,4)])
        m[0]=replace(m[0],breakdown={'score':ScoreContribution(.811,1,.811)})
        self.assertEqual(calculate_effective_earned_marks(m,q).earned,3.2)

    def test_tie_uses_paper_order_not_number_or_result_order(self):
        q, m = rows([(9,None,'A',5,7),(2,None,'A',5,7)])
        self.assertEqual(calculate_effective_earned_marks(m[::-1], q).or_groups['A']['selected_alternative'], 'Q9')

    def test_internal_precision_controls_selection_and_percentage(self):
        q, m = rows([(1,None,'A',5,7),(2,None,'A',5,7)])
        m = [replace(r, breakdown={'score': ScoreContribution(score,1,score)}) for r,score in zip(m,[.711,.719])]
        total = TotalMarksCalculator(RoundingPolicy(1)).calculate(m,q)
        self.assertEqual(total.or_groups['A']['selected_alternative'], 'Q2')
        self.assertEqual(total.awarded_marks, 5)
        self.assertEqual(total.percentage, 71.9)

    def test_full_example_percentage_and_maximum(self):
        q,m = rows([(1,None,'A',5.4,7),(2,None,'A',5.6,7),(3,None,'B',6,8),(4,None,'B',5.7,8)])
        total=TotalMarksCalculator(RoundingPolicy(1)).calculate(m,q)
        self.assertEqual(total.awarded_marks,11.6)
        self.assertEqual(total.exam_maximum_marks,15)
        self.assertAlmostEqual(total.percentage,77.3333,delta=.005)

    def test_zero_and_no_artificial_clamping(self):
        self.assertIsNone(TotalMarksCalculator(RoundingPolicy(1)).calculate([]).percentage)
        q,m=rows([(1,None,'A',8,7),(2,None,'A',5,7)])
        self.assertGreater(TotalMarksCalculator(RoundingPolicy(1)).calculate(m,q).percentage,100)

    def test_saved_real_evaluation(self):
        data=json.loads((Path(__file__).parent/'fixtures/or_earned_regression.json').read_text())
        questions, marks = [], []
        for row in data['questions']:
            number, part = row['question_id'][1:].split('(')
            identifier=QuestionId(int(number),part.rstrip(')'))
            saved=row['marks']
            questions.append(Question(identifier,int(number),'Question',saved['maximum'],alternative_group=row['alternative_group']))
            marks.append(MarksResult(identifier,saved['maximum'],saved['awarded'],saved['percentage'],saved['status'],
                                     {k:ScoreContribution(**v) for k,v in saved['breakdown'].items()}))
        total=TotalMarksCalculator(RoundingPolicy(1)).calculate(marks,questions)
        print('\nREAL REGRESSION:', data['source_report'])
        for name, group in total.or_groups.items(): print(name, group)
        print('NON-OR: 0; RAW EARNED:',sum(m.marks_awarded for m in marks))
        print('EFFECTIVE EARNED:',total.awarded_marks,'MAX:',total.exam_maximum_marks,'PERCENTAGE:',total.percentage,'RESULT COUNT:',len(marks))
        self.assertEqual(len(marks),8)
        self.assertEqual(total.exam_maximum_marks,15)
        self.assertEqual(total.or_groups['OR_1']['selected_alternative'],'Q2')
        self.assertEqual(total.or_groups['OR_2']['selected_alternative'],'Q3')
        self.assertEqual(total.awarded_marks,11.6)
        self.assertAlmostEqual(calculate_effective_earned_marks(marks,questions).earned,11.561814750407885)
        self.assertEqual(total.percentage,77.08)
