import unittest

from question_paper.structure_parser import StructureParser


class StructureParserTests(unittest.TestCase):
    def test_sections_marks_and_alternative_are_detected(self):
        paper = StructureParser().parse("""Example University
Subject: Databases
Maximum Marks: 10
SECTION A
Q1. (a) Define normalization. [2 marks] CO: 1
b) Explain 1NF. (3)
OR
Q2. a) Compare SQL and NoSQL. 5 marks
""")
        self.assertEqual(paper.exam.subject, "Databases")
        self.assertEqual(len(paper.sections[0].questions), 3)
        self.assertEqual(paper.sections[0].questions[0].marks, 2)
        self.assertEqual(paper.sections[0].questions[-1].alternative_group, "OR_1")

    def test_or_groups_each_side_without_creating_a_question(self):
        paper = StructureParser().parse("Q1(a) First. 2 marks\nQ1(b) Second. 2 marks\nOR\nQ2(a) Alternate. 2 marks\nQ2(b) Alternate second. 2 marks")
        groups = [question.alternative_group for question in paper.sections[0].questions]
        self.assertEqual(groups, ["OR_1", "OR_1", "OR_1", "OR_1"])

    def test_numbering_variant(self):
        paper = StructureParser().parse("1(i) Define TCP. 2 marks\n1(ii) Explain routing. 3 marks")
        self.assertEqual(len(paper.sections[0].questions), 2)
        self.assertEqual(paper.sections[0].questions[0].sub_question, "i")
