from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings


@dataclass(frozen=True, slots=True)
class EvaluationThresholds:
    correct: float
    mostly_correct: float
    partial: float
    concept: float
    relevance: float
    completeness: float

    @classmethod
    def from_settings(cls, settings: Settings) -> "EvaluationThresholds":
        return cls(settings.correct_threshold, settings.mostly_correct_threshold, settings.partial_threshold, settings.concept_threshold, settings.relevance_threshold, settings.completeness_threshold)
