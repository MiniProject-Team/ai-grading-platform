from __future__ import annotations

from .semantic_similarity import EmbeddingProvider, cosine_similarity


class RelevanceEvaluator:
    def __init__(self, embedder: EmbeddingProvider) -> None:
        self.embedder = embedder

    def evaluate(self, question_text: str, student_answer: str) -> float:
        question_vector, student_vector = self.embedder.encode([question_text, student_answer])
        return cosine_similarity(question_vector, student_vector)
