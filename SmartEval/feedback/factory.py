from __future__ import annotations

from config.settings import Settings

from .feedback_config import FeedbackConfig
from .feedback_service import FeedbackService
from .rule_based_feedback import RuleBasedFeedbackGenerator


def build_feedback_service(settings: Settings) -> FeedbackService:
    return FeedbackService(RuleBasedFeedbackGenerator(FeedbackConfig.from_settings(settings)))
