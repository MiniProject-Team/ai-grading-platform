import unittest
from pathlib import Path

from parsers.model_answer_parser import ModelAnswerParser
from parsers.student_answer_parser import StudentAnswerParser
from domain.value_objects.question_id import QuestionId


class AnswerParserTests(unittest.TestCase):
    def test_parses_model_answers(self):
        answers = ModelAnswerParser().parse("Q1.\nFirst model answer\n\nAnswer 2\nSecond model answer")
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])
        self.assertEqual(answers[1].answer_text, "Second model answer")

    def test_parses_fixture_model_answers_as_independent_subquestions(self):
        fixture = Path(__file__).resolve().parents[1] / "inputs" / "model_answer_fixture.txt"
        answers = ModelAnswerParser().parse(fixture.read_text(encoding="utf-8"))
        self.assertEqual(len(answers), 8)
        self.assertEqual([str(answer.question_id) for answer in answers], [
            "Q1(a)", "Q1(b)", "Q2(a)", "Q2(b)",
            "Q3(a)", "Q3(b)", "Q4(a)", "Q4(b)",
        ])
        self.assertTrue(all(answer.answer_text.strip() for answer in answers))
        self.assertNotEqual(answers[0].answer_text, answers[1].answer_text)
        self.assertNotEqual(answers[2].answer_text, answers[3].answer_text)
        self.assertNotEqual(answers[4].answer_text, answers[5].answer_text)
        self.assertNotEqual(answers[6].answer_text, answers[7].answer_text)
        self.assertFalse(any(str(answer.question_id) in {"Q1", "Q2", "Q3", "Q4"} for answer in answers))

    def test_segments_complete_student_answers(self):
        answers = StudentAnswerParser().parse("Question 1\nFirst complete answer\nwith another line\n\nQ2.\nSecond complete answer")
        self.assertEqual(answers[0].answer_text, "First complete answer\nwith another line")
        self.assertEqual(answers[1].answer_text, "Second complete answer")

    def test_parses_subquestion_heading_variants(self):
        expected = [QuestionId(1, "a")]
        for heading in ("Q1(a)", "Q.1(a)", "Q.1 (a)", "1(a)", "1 (a)", "Q1 (a)"):
            answers = StudentAnswerParser().parse(f"{heading}\nAnswer text", expected)
            self.assertEqual([str(answer.question_id) for answer in answers], ["Q1(a)"], heading)

    def test_preserves_separate_subquestion_answer_boundaries(self):
        expected = [QuestionId(1, "a"), QuestionId(1, "b")]
        answers = StudentAnswerParser().parse(
            "Q1(a)\nAnswer for part a\nQ1(b)\nAnswer for part b", expected,
        )
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1(a)", "Q1(b)"])
        self.assertEqual([answer.answer_text for answer in answers], ["Answer for part a", "Answer for part b"])

    def test_ignores_arbitrary_numbers_and_unknown_question_ids(self):
        expected = [QuestionId(1, "a"), QuestionId(1, "b")]
        answers = StudentAnswerParser().parse(
            "Q5\nUnknown\nStep 1\n[4]\n2026\nQ1(a)\nValid answer", expected,
        )
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1(a)"])
        self.assertNotIn("Q5", {str(answer.question_id) for answer in answers})

    def test_parses_all_eight_expected_subquestions(self):
        expected = [QuestionId(number, subpart) for number in range(1, 5) for subpart in ("a", "b")]
        text = "\n".join(f"Q{question_id.number}({question_id.subpart})\nAnswer {question_id}" for question_id in expected)
        answers = StudentAnswerParser().parse(text, expected)
        self.assertEqual([str(answer.question_id) for answer in answers], [str(question_id) for question_id in expected])
        self.assertTrue(all(answer.answer_text.strip() for answer in answers))

    def test_accepts_common_ocr_answer_heading_variants(self):
        answers = StudentAnswerParser().parse("Ans 1: First answer\nAnswer No. 2 Second answer")
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])

    def test_uses_low_confidence_sequential_fallback_when_headings_are_absent(self):
        answers = StudentAnswerParser().parse("First answer\n\nSecond answer", [QuestionId(1), QuestionId(2)])
        self.assertEqual([str(answer.question_id) for answer in answers], ["Q1", "Q2"])
        self.assertTrue(all(answer.mapping_method == "sequential_fallback" for answer in answers))
