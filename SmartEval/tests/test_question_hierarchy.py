import unittest

from parsers.section_parser import NumberedSectionParser, normalize_question_id
from parsers.question_parser import QuestionParser
from question_paper.canonical import QuestionHierarchyParser


class QuestionHierarchyTests(unittest.TestCase):
    PAPER = """Q.1\n a) First\n b) Second\nOR\nQ.2\n a) Third\n b) Fourth\nQ.3\n a) Fifth\n b) Sixth\nOR\nQ.4\n a) Seventh\n b) Eighth\n"""

    def test_hierarchy_keeps_unique_top_questions_and_or_groups(self):
        questions = QuestionHierarchyParser().parse(self.PAPER)
        self.assertEqual([q.id for q in questions], ["Q1", "Q2", "Q3", "Q4"])
        self.assertEqual([q.id for q in questions[-1].subquestions], ["Q4(a)", "Q4(b)"])
        self.assertEqual([q.alternative_group for q in questions], ["OR_1", "OR_1", "OR_2", "OR_2"])

    def test_marks_cell_is_not_a_question_header(self):
        sections = NumberedSectionParser().parse("Q4. Explain NLP\n4 marks\nCO 2")
        self.assertEqual(len(sections), 1)

    def test_normalization(self):
        self.assertEqual(normalize_question_id("Q . 4"), "Q4")
        self.assertEqual(normalize_question_id("4(a)"), "Q4(a)")

    def test_true_duplicate_fails(self):
        with self.assertRaisesRegex(ValueError, "Duplicate question ID"):
            QuestionHierarchyParser().parse("Q4. Question A\nQ4. Question B")

    def test_legacy_adapter_receives_unique_top_level_ids(self):
        questions = QuestionParser().parse(self.PAPER)
        self.assertEqual([str(question.question_id) for question in questions], ["Q1", "Q2", "Q3", "Q4"])

    def test_canonical_result_is_used_even_when_pdf_layout_hides_subquestion_rows(self):
        questions = QuestionParser().parse("Q1. First\nQ2. Second\nQ3. Third\nQ4. Fourth\n4 marks")
        self.assertEqual([str(question.question_id) for question in questions], ["Q1", "Q2", "Q3", "Q4"])

    def test_table_co_values_are_not_question_headers(self):
        questions = QuestionParser().parse("Q4\na) First\n4\n703.2\nb) Second\n4\n703.2")
        self.assertEqual([str(question.question_id) for question in questions], ["Q4"])
