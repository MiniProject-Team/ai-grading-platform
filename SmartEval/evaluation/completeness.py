from __future__ import annotations

from .concept_coverage import ConceptCoverageEvaluator


class CompletenessEvaluator:
    """Completeness is expected-concept coverage, not answer length."""
    def __init__(self, concept_evaluator: ConceptCoverageEvaluator) -> None:
        self.concept_evaluator = concept_evaluator

    def evaluate(self, model_answer: str, student_answer: str) -> float:
        return self.concept_evaluator.evaluate(model_answer, student_answer)
