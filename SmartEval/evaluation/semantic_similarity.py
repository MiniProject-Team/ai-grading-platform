"""Replaceable embedding-based semantic similarity evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging

import numpy as np


class EmbeddingProvider(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger("smarteval")

    def encode(self, texts: list[str]) -> np.ndarray:
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.logger.info("Loading semantic model '%s'", self.model_name)
                self.model = SentenceTransformer(self.model_name)
            except Exception as error:
                raise RuntimeError(f"Unable to load semantic model '{self.model_name}': {error}") from error
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype=float)


class SemanticSimilarityEvaluator(ABC):
    @abstractmethod
    def evaluate(self, model_answer: str, student_answer: str) -> float: ...


class EmbeddingSemanticSimilarityEvaluator(SemanticSimilarityEvaluator):
    def __init__(self, embedder: EmbeddingProvider) -> None:
        self.embedder = embedder

    def evaluate(self, model_answer: str, student_answer: str) -> float:
        model_vector, student_vector = self.embedder.encode([model_answer, student_answer])
        return cosine_similarity(model_vector, student_vector)


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0:
        return 0.0
    return max(0.0, min(1.0, float(np.dot(left, right) / denominator)))
