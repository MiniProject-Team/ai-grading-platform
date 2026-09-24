from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(_ResponseModel):
    status: Literal["ok"]
    service: Literal["SmartEval"]


class EvaluationMetricsResponse(_ResponseModel):
    semantic_similarity: float | None
    concept_coverage: float | None
    relevance: float | None
    completeness: float | None
    status: str
    explanation: str


class ScoreContributionResponse(_ResponseModel):
    score: float
    weight: float
    contribution: float


class MarksResponse(_ResponseModel):
    awarded: float | None
    maximum: int | None
    percentage: float | None
    status: str
    note: str | None
    breakdown: dict[str, ScoreContributionResponse]


class FeedbackResponse(_ResponseModel):
    strengths: list[str]
    missing_concepts: list[str]
    weak_areas: list[str]
    improvement_suggestions: list[str]
    overall_feedback: str


class QuestionResultResponse(_ResponseModel):
    question_id: str
    question: str
    max_marks: int | None
    alternative_group: str | None = None
    student_answer: str
    model_answer: str | None
    evaluation: EvaluationMetricsResponse
    marks: MarksResponse
    feedback: FeedbackResponse


class SummaryResponse(_ResponseModel):
    total_questions: int
    evaluated_questions: int
    unanswered_questions: int
    missing_model_answers: int
    awarded_marks: float
    evaluated_maximum_marks: int
    exam_maximum_marks: int
    percentage: float | None


class StatisticsResponse(_ResponseModel):
    average_semantic_similarity: float | None
    average_concept_coverage: float | None
    average_relevance: float | None
    average_completeness: float | None
    average_question_percentage: float | None
    highest_score_question: str | None
    lowest_score_question: str | None
    status_distribution: dict[str, int]


class EvaluationResponse(_ResponseModel):
    evaluation_id: str
    status: Literal["complete", "partially_evaluated", "failed"]
    student_information: dict[str, str] | None
    exam_information: dict[str, str | int] | None
    question_results: list[QuestionResultResponse]
    summary: SummaryResponse
    statistics: StatisticsResponse
    top_strengths: list[str]
    common_weaknesses: list[str]
    overall_improvement_suggestions: list[str]
    warnings: list[str]
    metadata: dict[str, str]


class EvaluationHistoryItemResponse(_ResponseModel):
    evaluation_id: str
    status: Literal["complete", "partially_evaluated", "failed"]
    student_information: dict[str, str] | None
    exam_information: dict[str, str | int] | None
    summary: SummaryResponse
    created_at: str | None


class EvaluationListResponse(_ResponseModel):
    items: list[EvaluationHistoryItemResponse]
    total: int
    page: int
    page_size: int


class ErrorDetailResponse(_ResponseModel):
    code: str
    message: str


class ErrorResponse(_ResponseModel):
    status: Literal["error", "failed"]
    evaluation_id: str | None = None
    error: ErrorDetailResponse
