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

    def test_legacy_adapter_flattens_subquestions_with_individual_marks_and_or_groups(self):
        questions = QuestionParser().parse(self.PAPER)
        self.assertEqual([str(question.question_id) for question in questions], [
            "Q1(a)", "Q1(b)", "Q2(a)", "Q2(b)",
            "Q3(a)", "Q3(b)", "Q4(a)", "Q4(b)",
        ])
        self.assertEqual([question.max_marks for question in questions], [None] * 8)

    def test_adapter_keeps_parent_only_questions_compatible(self):
        questions = QuestionParser().parse("Q1. First question [4]")
        self.assertEqual([str(question.question_id) for question in questions], ["Q1"])
        self.assertEqual(questions[0].max_marks, 4)

    def test_adapter_extracts_marks_and_metadata_per_child(self):
        paper = """Q.1 a)
Explain first.
[4]

b)
Explain second.
[3]

OR

Q.2 a)
Explain alternate first.
[4]

b)
Explain alternate second.
[3]
"""
        questions = QuestionParser().parse(paper)
        self.assertEqual([str(question.question_id) for question in questions], ["Q1(a)", "Q1(b)", "Q2(a)", "Q2(b)"])
        self.assertEqual([question.max_marks for question in questions], [4, 3, 4, 3])
        self.assertEqual([question.alternative_group for question in questions], ["OR_1"] * 4)
        self.assertEqual(sum(question.max_marks or 0 for question in questions), 14)
        self.assertEqual([question.question_text for question in questions], [
            "Explain first.", "Explain second.", "Explain alternate first.", "Explain alternate second.",
        ])

    def test_exact_subquestion_fixture_returns_eight_items_and_thirty_marks(self):
        paper = """Q.1 a)
Explain the steps involved in text preprocessing and normalization tokenization, stop-word removal, stemming, and lemmatization.
Illustrate each step with a suitable example sentence
[4]

b)
Explain the concept of text preprocessing with example.
[3]

OR

Q.2 a)
Define Natural Language Processing. Explain its scope and describe any four real-world applications of NLP.
[4]

b)
Define Linguistics. Explain the concept in detail.
[3]

Q.3 a)
Explain test categorization of test in detail.
[4]

b)
Explain various n-gram model in detail.
[4]

OR

Q.4 a)
Explain the Naive Bayes algorithm for text classification.
[4]

b)
Compare Decision Tree and Support Vector Machine classifiers.
[4]
"""
        questions = QuestionParser().parse(paper)
        self.assertEqual(len(questions), 8)
        self.assertEqual([str(question.question_id) for question in questions], [
            "Q1(a)", "Q1(b)", "Q2(a)", "Q2(b)",
            "Q3(a)", "Q3(b)", "Q4(a)", "Q4(b)",
        ])
        self.assertEqual([question.max_marks for question in questions], [4, 3, 4, 3, 4, 4, 4, 4])
        self.assertEqual(sum(question.max_marks or 0 for question in questions), 30)
        self.assertEqual([question.alternative_group for question in questions], [
            "OR_1", "OR_1", "OR_1", "OR_1", "OR_2", "OR_2", "OR_2", "OR_2",
        ])
        self.assertFalse(any(str(question.question_id) in {"Q1", "Q2", "Q3", "Q4"} for question in questions))
        self.assertFalse(any(str(question.question_id) in {f"Q{number}" for number in range(5, 14)} for question in questions))
        self.assertNotIn("[4]", questions[0].question_text)
        self.assertNotIn("[3]", questions[1].question_text)

    def test_canonical_result_is_used_even_when_pdf_layout_hides_subquestion_rows(self):
        questions = QuestionParser().parse("Q1. First\nQ2. Second\nQ3. Third\nQ4. Fourth\n4 marks")
        self.assertEqual([str(question.question_id) for question in questions], ["Q1", "Q2", "Q3", "Q4"])

    def test_table_co_values_are_not_question_headers(self):
        questions = QuestionParser().parse("Q4\na) First\n4\n703.2\nb) Second\n4\n703.2")
        self.assertEqual([str(question.question_id) for question in questions], ["Q4(a)", "Q4(b)"])
        self.assertFalse(any(str(question.question_id) in {f"Q{number}" for number in range(5, 704)} for question in questions))
