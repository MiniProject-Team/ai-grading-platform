"""Concept coverage based on sentence-level embedding alignment."""

from __future__ import annotations

import re

from .semantic_similarity import EmbeddingProvider, cosine_similarity


def split_concepts(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


class ConceptCoverageEvaluator:
    def __init__(self, embedder: EmbeddingProvider) -> None:
        self.embedder = embedder

    def evaluate(self, model_answer: str, student_answer: str) -> float:
        expected = split_concepts(model_answer)
        observed = split_concepts(student_answer)
        if not expected or not observed:
            return 0.0
        expected_vectors = self.embedder.encode(expected)
        observed_vectors = self.embedder.encode(observed)
        matches = [max(cosine_similarity(expected_vector, observed_vector) for observed_vector in observed_vectors) for expected_vector in expected_vectors]
        return float(sum(matches) / len(matches))
