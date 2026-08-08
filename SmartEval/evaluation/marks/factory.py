from __future__ import annotations

from config.settings import Settings

from .marks_calculator import WeightedMarksCalculator
from .rounding import RoundingPolicy
from .scoring_config import ScoringWeights, WeightedScoringStrategy


def build_marks_calculator(settings: Settings) -> WeightedMarksCalculator:
    rounding = RoundingPolicy(settings.marks_decimal_places)
    return WeightedMarksCalculator(WeightedScoringStrategy(ScoringWeights.from_settings(settings)), rounding)
