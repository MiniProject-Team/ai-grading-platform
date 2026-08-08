from __future__ import annotations

import numpy as np

from evaluation.semantic_similarity import EmbeddingProvider


class StaticEmbeddingProvider(EmbeddingProvider):
    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray([self.vectors[text] for text in texts], dtype=float)
