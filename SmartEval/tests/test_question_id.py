from __future__ import annotations

import unittest

from domain.value_objects.question_id import QuestionId


class QuestionIdTests(unittest.TestCase):
    def test_string_representation_preserves_parent_and_subpart_forms(self):
        self.assertEqual(str(QuestionId(1)), "Q1")
        self.assertEqual(str(QuestionId(1, "a")), "Q1(a)")
        self.assertEqual(str(QuestionId(1, "b")), "Q1(b)")

    def test_equality_distinguishes_subparts(self):
        self.assertNotEqual(QuestionId(1), QuestionId(1, "a"))
        self.assertNotEqual(QuestionId(1, "a"), QuestionId(1, "b"))
        self.assertEqual(QuestionId(1, "a"), QuestionId(1, "a"))

    def test_equivalent_ids_have_equal_stable_hashes(self):
        self.assertEqual(hash(QuestionId(1, "a")), hash(QuestionId(1, "a")))
        self.assertEqual({QuestionId(1, "a")}, {QuestionId(1, "a")})

    def test_subpart_is_normalized(self):
        self.assertEqual(str(QuestionId(1, "A")), "Q1(a)")

    def test_zero_and_negative_numbers_are_rejected(self):
        for number in (0, -1):
            with self.assertRaisesRegex(ValueError, "Question ID must be positive"):
                QuestionId(number)


if __name__ == "__main__":
    unittest.main()
