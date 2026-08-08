from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from config.settings import Settings
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.marks_result import ScoreContribution


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    semantic: float
    concept: float
    relevance: float
    completeness: float

    def __post_init__(self) -> None:
        weights = (self.semantic, self.concept, self.relevance, self.completeness)
        if any(weight < 0 or weight > 1 for weight in weights):
            raise ValueError("All scoring weights must be between 0 and 1")
        if not isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError("Scoring weights must sum to exactly 1.0")

    @classmethod
    def from_settings(cls, settings: Settings) -> "ScoringWeights":
        return cls(settings.semantic_weight, settings.concept_weight, settings.relevance_weight, settings.completeness_weight)


class ScoringStrategy:
    def calculate_score(self, evaluation: EvaluationResult) -> tuple[float, dict[str, ScoreContribution]]:
        raise NotImplementedError


class WeightedScoringStrategy(ScoringStrategy):
    def __init__(self, weights: ScoringWeights) -> None:
        self.weights = weights

    def calculate_score(self, evaluation: EvaluationResult) -> tuple[float, dict[str, ScoreContribution]]:
        values = {
            "semantic_similarity": (evaluation.semantic_similarity, self.weights.semantic),
            "concept_coverage": (evaluation.concept_coverage, self.weights.concept),
            "relevance": (evaluation.relevance, self.weights.relevance),
            "completeness": (evaluation.completeness, self.weights.completeness),
        }
        breakdown = {}
        for name, (score, weight) in values.items():
            if score is None or not 0 <= score <= 1:
                raise ValueError(f"{name} must be a score between 0 and 1")
            breakdown[name] = ScoreContribution(score, weight, score * weight)
        return sum(value.contribution for value in breakdown.values()), breakdown
