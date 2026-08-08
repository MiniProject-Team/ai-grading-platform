from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.question_id import QuestionId


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Phase 5 semantic signals; marks and feedback belong to later phases."""
    question_id: QuestionId
    semantic_similarity: float | None
    concept_coverage: float | None
    relevance: float | None
    completeness: float | None
    status: str
    explanation: str
