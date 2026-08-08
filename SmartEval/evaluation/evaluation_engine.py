"""Coordinate semantic signals for one mapped answer without assigning marks."""

from __future__ import annotations

import logging
import time

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_result import EvaluationResult

from .completeness import CompletenessEvaluator
from .concept_coverage import ConceptCoverageEvaluator
from .relevance import RelevanceEvaluator
from .semantic_similarity import SemanticSimilarityEvaluator
from .thresholds import EvaluationThresholds


class EvaluationEngine:
    def __init__(
        self,
        semantic_evaluator: SemanticSimilarityEvaluator,
        concept_evaluator: ConceptCoverageEvaluator,
        relevance_evaluator: RelevanceEvaluator,
        completeness_evaluator: CompletenessEvaluator,
        thresholds: EvaluationThresholds,
    ) -> None:
        self.semantic_evaluator = semantic_evaluator
        self.concept_evaluator = concept_evaluator
        self.relevance_evaluator = relevance_evaluator
        self.completeness_evaluator = completeness_evaluator
        self.thresholds = thresholds
        self.logger = logging.getLogger("smarteval")

    def evaluate(self, item: EvaluationItem) -> EvaluationResult:
        question_id = item.question.question_id
        if item.model_answer_missing:
            self.logger.error("Evaluation skipped for %s: model answer missing", question_id)
            return EvaluationResult(question_id, None, None, None, None, "model_answer_missing", "Model answer unavailable; evaluation was not performed.")
        if item.student_answer_missing:
            self.logger.info("Evaluation skipped for %s: no student answer", question_id)
            return EvaluationResult(question_id, 0.0, 0.0, 0.0, 0.0, "no_answer", "No student answer was detected.")

        started = time.perf_counter()
        self.logger.info("Evaluation started for %s", question_id)
        model_text = item.model_answer.answer_text
        student_text = item.student_answer.answer_text
        semantic = self.semantic_evaluator.evaluate(model_text, student_text)
        coverage = self.concept_evaluator.evaluate(model_text, student_text)
        relevance = self.relevance_evaluator.evaluate(item.question.question_text, student_text)
        completeness = self.completeness_evaluator.evaluate(model_text, student_text)
        status = self._classify(semantic, coverage, relevance, completeness)
        self.logger.info(
            "Evaluation completed for %s in %.2fs: semantic=%.3f coverage=%.3f relevance=%.3f completeness=%.3f status=%s",
            question_id, time.perf_counter() - started, semantic, coverage, relevance, completeness, status,
        )
        return EvaluationResult(question_id, semantic, coverage, relevance, completeness, status, self._explanation(status))

    def _classify(self, semantic: float, coverage: float, relevance: float, completeness: float) -> str:
        if relevance < self.thresholds.partial:
            return "irrelevant"
        average = (semantic + coverage + relevance + completeness) / 4
        if average >= self.thresholds.correct and coverage >= self.thresholds.concept and completeness >= self.thresholds.completeness and relevance >= self.thresholds.relevance:
            return "correct"
        if average >= self.thresholds.mostly_correct:
            return "mostly_correct"
        if average >= self.thresholds.partial:
            return "partially_correct"
        return "irrelevant"

    @staticmethod
    def _explanation(status: str) -> str:
        return {
            "correct": "The answer strongly aligns with the expected concepts and question.",
            "mostly_correct": "The answer aligns with most expected concepts but may omit some detail.",
            "partially_correct": "The answer addresses part of the expected content.",
            "irrelevant": "The answer has low alignment with the question or expected content.",
        }[status]
