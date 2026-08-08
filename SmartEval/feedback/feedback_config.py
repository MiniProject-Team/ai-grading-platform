from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings


@dataclass(frozen=True, slots=True)
class FeedbackConfig:
    excellent_threshold: float
    good_threshold: float
    partial_threshold: float
    low_threshold: float
    strength_threshold: float
    weakness_threshold: float
    max_strengths: int = 3
    max_missing_concepts: int = 3
    max_weak_areas: int = 2
    max_suggestions: int = 2

    def __post_init__(self) -> None:
        thresholds = (
            self.excellent_threshold,
            self.good_threshold,
            self.partial_threshold,
            self.low_threshold,
            self.strength_threshold,
            self.weakness_threshold,
        )
        if any(not 0 <= threshold <= 1 for threshold in thresholds):
            raise ValueError("Feedback thresholds must be between 0 and 1")
        if not self.excellent_threshold >= self.good_threshold >= self.partial_threshold >= self.low_threshold:
            raise ValueError("Feedback score thresholds must descend from excellent to low")
        if self.strength_threshold < self.weakness_threshold:
            raise ValueError("Feedback strength threshold must be at least the weakness threshold")
        if any(limit < 1 for limit in (self.max_strengths, self.max_missing_concepts, self.max_weak_areas, self.max_suggestions)):
            raise ValueError("Feedback result limits must be positive")

    @classmethod
    def from_settings(cls, settings: Settings) -> "FeedbackConfig":
        return cls(
            excellent_threshold=settings.feedback_excellent_threshold,
            good_threshold=settings.feedback_good_threshold,
            partial_threshold=settings.feedback_partial_threshold,
            low_threshold=settings.feedback_low_threshold,
            strength_threshold=settings.feedback_strength_threshold,
            weakness_threshold=settings.feedback_weakness_threshold,
        )

    def score_band(self, normalized_score: float | None) -> str | None:
        if normalized_score is None:
            return None
        if not 0 <= normalized_score <= 1:
            raise ValueError("Normalized score must be between 0 and 1")
        if normalized_score >= self.excellent_threshold:
            return "excellent"
        if normalized_score >= self.good_threshold:
            return "good"
        if normalized_score >= self.partial_threshold:
            return "partial"
        if normalized_score >= self.low_threshold:
            return "low"
        return "minimal"
