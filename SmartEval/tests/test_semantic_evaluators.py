import unittest

from evaluation.completeness import CompletenessEvaluator
from evaluation.concept_coverage import ConceptCoverageEvaluator
from evaluation.relevance import RelevanceEvaluator
from evaluation.semantic_similarity import EmbeddingSemanticSimilarityEvaluator

from embedding_fakes import StaticEmbeddingProvider


class SemanticEvaluatorTests(unittest.TestCase):
    def test_similar_and_ocr_noisy_answers_remain_semantically_close(self):
        provider = StaticEmbeddingProvider({
            "model": [1.0, 0.0], "paraphrase": [0.95, 0.05], "ocr noisy": [0.92, 0.08], "unrelated": [0.0, 1.0],
        })
        evaluator = EmbeddingSemanticSimilarityEvaluator(provider)
        self.assertGreater(evaluator.evaluate("model", "paraphrase"), 0.9)
        self.assertGreater(evaluator.evaluate("model", "ocr noisy"), 0.85)
        self.assertLess(evaluator.evaluate("model", "unrelated"), 0.1)

    def test_coverage_and_completeness_are_concept_oriented(self):
        provider = StaticEmbeddingProvider({
            "definition.": [1.0, 0.0], "patterns.": [0.0, 1.0], "student definition.": [0.95, 0.05],
        })
        coverage = ConceptCoverageEvaluator(provider)
        score = coverage.evaluate("definition. patterns.", "student definition.")
        self.assertGreater(score, 0.45)
        self.assertLess(score, 0.60)
        self.assertEqual(CompletenessEvaluator(coverage).evaluate("definition. patterns.", "student definition."), score)

    def test_relevance_is_low_for_an_unrelated_answer(self):
        provider = StaticEmbeddingProvider({"question": [1.0, 0.0], "relevant": [0.9, 0.1], "unrelated": [0.0, 1.0]})
        evaluator = RelevanceEvaluator(provider)
        self.assertGreater(evaluator.evaluate("question", "relevant"), 0.8)
        self.assertLess(evaluator.evaluate("question", "unrelated"), 0.1)
