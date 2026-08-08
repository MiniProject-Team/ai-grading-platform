from __future__ import annotations

from config.settings import Settings

from .completeness import CompletenessEvaluator
from .concept_coverage import ConceptCoverageEvaluator
from .evaluation_engine import EvaluationEngine
from .relevance import RelevanceEvaluator
from .semantic_similarity import EmbeddingSemanticSimilarityEvaluator, SentenceTransformerEmbeddingProvider
from .thresholds import EvaluationThresholds


def build_evaluation_engine(settings: Settings) -> EvaluationEngine:
    embedder = SentenceTransformerEmbeddingProvider(settings.semantic_model_name)
    concept_evaluator = ConceptCoverageEvaluator(embedder)
    return EvaluationEngine(
        semantic_evaluator=EmbeddingSemanticSimilarityEvaluator(embedder),
        concept_evaluator=concept_evaluator,
        relevance_evaluator=RelevanceEvaluator(embedder),
        completeness_evaluator=CompletenessEvaluator(concept_evaluator),
        thresholds=EvaluationThresholds.from_settings(settings),
    )
