from __future__ import annotations

from collections import Counter

from domain.entities.evaluation_report import EvaluationStatistics, QuestionEvaluationResult


class StatisticsBuilder:
    _STATUSES = (
        "correct",
        "mostly_correct",
        "partially_correct",
        "irrelevant",
        "no_answer",
        "model_answer_missing",
    )

    def build(self, question_results: list[QuestionEvaluationResult]) -> EvaluationStatistics:
        if not question_results:
            raise ValueError("Statistics require at least one question result")
        statuses = Counter(result.evaluation.status for result in question_results)
        scored_results = [result for result in question_results if result.marks.percentage is not None]
        return EvaluationStatistics(
            average_semantic_similarity=self._average([result.evaluation.semantic_similarity for result in question_results]),
            average_concept_coverage=self._average([result.evaluation.concept_coverage for result in question_results]),
            average_relevance=self._average([result.evaluation.relevance for result in question_results]),
            average_completeness=self._average([result.evaluation.completeness for result in question_results]),
            average_question_percentage=self._average([result.marks.percentage for result in scored_results]),
            highest_score_question=max(scored_results, key=lambda result: result.marks.percentage).question_id if scored_results else None,
            lowest_score_question=min(scored_results, key=lambda result: result.marks.percentage).question_id if scored_results else None,
            status_distribution={status: statuses.get(status, 0) for status in self._STATUSES},
        )

    @staticmethod
    def _average(values: list[float | None]) -> float | None:
        usable = [value for value in values if value is not None]
        return round(sum(usable) / len(usable), 4) if usable else None
