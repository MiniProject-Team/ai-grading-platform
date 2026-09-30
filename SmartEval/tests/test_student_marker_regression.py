from pathlib import Path
import unittest

from domain.value_objects.question_id import QuestionId
from parsers.student_answer_parser import HEADING_PATTERN, StudentAnswerParser


class StudentMarkerRegressionTests(unittest.TestCase):
    def setUp(self):
        self.parser = StudentAnswerParser()
        self.expected = [QuestionId(n,p) for n in range(1,5) for p in ('a','b')]

    def test_normal_headings(self):
        answers=self.parser.parse('Q.1 (a)\nFirst answer\nQ.1 (b)\nSecond answer',self.expected)
        self.assertEqual([a.question_id for a in answers],self.expected[:2])

    def test_one_physical_heading_produces_one_candidate(self):
        # The parser uses one anchored pattern, not overlapping pattern passes.
        line='Q.1 (a) Heading'
        self.assertEqual(len(list(HEADING_PATTERN.finditer(line))),1)
        self.assertEqual(len(self.parser.parse(line+'\nAnswer',self.expected)),1)

    def test_inline_reference_is_preserved_in_answer(self):
        answers=self.parser.parse('Q.1 (a)\nThe answer refers to Q1(b) as an example.',self.expected)
        self.assertEqual(len(answers),1)
        self.assertIn('Q1(b)',answers[0].answer_text)

    def test_genuine_duplicate_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate question IDs'):
            self.parser.parse('Q.1 (a)\nFirst answer\nQ.1 (a)\nSecond answer',self.expected)

    def test_numbered_prose_does_not_split_subquestion(self):
        text='Q.3 (b) N-grams\n2. Bigram model\nExplanation\n4. Apply smoothing\nMore explanation'
        answers=self.parser.parse(text,self.expected)
        self.assertEqual([str(a.question_id) for a in answers],['Q3(b)'])
        self.assertIn('2. Bigram model',answers[0].answer_text)
        self.assertIn('4. Apply smoothing',answers[0].answer_text)

    def test_complete_delimited_subpart_remains_supported(self):
        for heading in ('Q1.a) Heading','1.a. Heading','Q1.a Heading','1(a) Heading'):
            with self.subTest(heading=heading):
                self.assertEqual(self.parser.parse(heading,self.expected)[0].question_id,QuestionId(1,'a'))

    def test_top_level_heading_does_not_consume_first_body_letter(self):
        answers=self.parser.parse('Q1. Artificial intelligence\nQ2. Bigram model',[QuestionId(1),QuestionId(2)])
        self.assertEqual([a.answer_text for a in answers],['Artificial intelligence','Bigram model'])

    def test_exact_saved_fixture(self):
        text=(Path(__file__).parent/'fixtures/student_duplicate_markers.txt').read_text(encoding='utf-8')
        self.assertEqual(len(text),17004)
        answers=self.parser.parse(text,self.expected)
        self.assertEqual([a.question_id for a in answers],self.expected)
        # Every real section body must be retained, including numbered prose.
        headers=[i for i,line in enumerate(text.splitlines()) if line.startswith('Q.')]
        lines=text.splitlines()
        for index,answer in enumerate(answers):
            start=headers[index]
            end=headers[index+1] if index+1<len(headers) else len(lines)
            body=HEADING_PATTERN.match(lines[start]).group('body').strip()
            expected_text='\n'.join([body,*lines[start+1:end]]).strip()
            self.assertEqual(answer.answer_text,expected_text)
