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

    def test_chrome_bare_subpart_headings_preserve_numbered_prose(self):
        text = ('Q.3 a) Text categorization\nDefinition and applications.\n'
                'Q.3 b) N-gram models\n1. Unigram (N=1): each word is independent.\n'
                '2. Bigram (N=2): depends on one previous word.\n'
                '3. Trigram (N=3): depends on two previous words.')
        answers = self.parser.parse(text, self.expected)
        self.assertEqual([str(a.question_id) for a in answers], ['Q3(a)', 'Q3(b)'])
        self.assertEqual(answers[1].answer_text, text.split('Q.3 b) ')[1])

    def test_duplicate_bare_subparts_are_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate question IDs'):
            self.parser.parse('Q.3 a) First answer\nQ.3 a) Second answer', self.expected)

    def test_zero_numbers_and_probability_values_preserve_answer_content(self):
        text = ('Q.4 a) Naive Bayes\nSpam score 0.00103 > Ham score\n'
                '0.00010 (with Laplace smoothing), so it is Spam.\n'
                '0) A numbered note\nQ0 Invalid heading\nQ.4 b) SVM answer')
        answers = self.parser.parse(text, self.expected)
        self.assertEqual([a.question_id for a in answers], self.expected[-2:])
        self.assertEqual(answers[0].answer_text, text.split('Q.4 a) ')[1].split('\nQ.4 b)')[0])

    def test_ocr_one_confusion_in_explicit_subquestion_headings(self):
        for heading in ('Q.l b)', 'Q.I b)', 'Question l(b)', 'Answer I (b)'):
            with self.subTest(heading=heading):
                answers = self.parser.parse('Q.1 a) First answer\n' + heading + ' Second answer', self.expected)
                self.assertEqual([a.question_id for a in answers], self.expected[:2])
                self.assertEqual(answers[1].answer_text, 'Second answer')

    def test_bare_ocr_letters_remain_answer_content(self):
        text = 'Q.1 a) First answer\nl b) A list item\nI (b) Another list item'
        answers = self.parser.parse(text, self.expected)
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0].answer_text, text.split('Q.1 a) ')[1])

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
