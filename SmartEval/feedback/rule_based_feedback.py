from __future__ import annotations

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer

from .feedback_config import FeedbackConfig
from .feedback_generator import FeedbackGenerator


class RuleBasedFeedbackGenerator(FeedbackGenerator):
    """Deterministic feedback grounded only in marks and Phase 5 signals."""

    _SUPPORTED_STATUSES = frozenset({
        "correct", "mostly_correct", "partially_correct", "irrelevant", "no_answer", "model_answer_missing",
    })

    def __init__(self, config: FeedbackConfig) -> None:
        self.config = config

    def generate(
        self,
        question: Question | None,
        model_answer: ModelAnswer | None,
        student_answer: StudentAnswer | None,
        evaluation_result: EvaluationResult | None,
        marks_result: MarksResult | None,
    ) -> FeedbackResult:
        self._validate_inputs(question, model_answer, student_answer, evaluation_result, marks_result)
        assert question is not None
        assert evaluation_result is not None
        assert marks_result is not None

        status = evaluation_result.status
        if status == "no_answer":
            return self._special_result(question, marks_result, status, "No answer was detected for this question.")
        if status == "model_answer_missing":
            return self._special_result(question, marks_result, status, "Evaluation could not be completed because the model answer is unavailable.")

        scores = {
            "semantic": evaluation_result.semantic_similarity,
            "coverage": evaluation_result.concept_coverage,
            "relevance": evaluation_result.relevance,
            "completeness": evaluation_result.completeness,
        }
        if any(score is None for score in scores.values()):
            raise ValueError(f"Evaluation result for {question.question_id} is missing required metric values")
        strengths = self._strengths(scores, status)
        missing_concepts = self._missing_concepts(scores["coverage"])
        weak_areas = self._weak_areas(scores, status)
        suggestions = self._suggestions(scores, status, self._normalized_score(marks_result))
        return FeedbackResult(
            question_id=question.question_id,
            marks_awarded=marks_result.marks_awarded,
            max_marks=marks_result.max_marks,
            status=status,
            strengths=tuple(strengths[: self.config.max_strengths]),
            missing_concepts=tuple(missing_concepts[: self.config.max_missing_concepts]),
            weak_areas=tuple(weak_areas[: self.config.max_weak_areas]),
            improvement_suggestions=tuple(suggestions[: self.config.max_suggestions]),
            overall_feedback=self._overall(status, self._normalized_score(marks_result)),
        )

    def _validate_inputs(
        self,
        question: Question | None,
        model_answer: ModelAnswer | None,
        student_answer: StudentAnswer | None,
        evaluation: EvaluationResult | None,
        marks: MarksResult | None,
    ) -> None:
        if question is None:
            raise ValueError("Feedback generation requires a question")
        if evaluation is None:
            raise ValueError(f"Feedback generation requires an EvaluationResult for {question.question_id}")
        if marks is None:
            raise ValueError(f"Feedback generation requires a MarksResult for {question.question_id}")
        if student_answer is None:
            raise ValueError(f"Feedback generation requires a StudentAnswer for {question.question_id}")
        if evaluation.question_id != question.question_id or marks.question_id != question.question_id:
            raise ValueError("Question, evaluation result, and marks result IDs must match")
        if student_answer.question_id != question.question_id:
            raise ValueError("Question and student answer IDs must match")
        if evaluation.status not in self._SUPPORTED_STATUSES:
            raise ValueError(f"Unsupported evaluation status: {evaluation.status}")
        if marks.evaluation_status not in {evaluation.status, "max_marks_unavailable"}:
            raise ValueError("Evaluation and marks statuses must match")
        if marks.max_marks != question.max_marks:
            raise ValueError("Question and marks result maximum marks must match")
        if evaluation.status == "model_answer_missing":
            return
        if model_answer is None:
            raise ValueError(f"Feedback generation requires a ModelAnswer for {question.question_id}")
        if model_answer.question_id != question.question_id:
            raise ValueError("Question and model answer IDs must match")

    def _special_result(self, question: Question, marks: MarksResult, status: str, message: str) -> FeedbackResult:
        suggestions = () if status == "model_answer_missing" else ("Provide an answer that directly addresses the question.",)
        return FeedbackResult(question.question_id, marks.marks_awarded, marks.max_marks, status, (), (), (), suggestions, message)

    def _strengths(self, scores: dict[str, float | None], status: str) -> list[str]:
        strengths: list[str] = []
        if status == "correct":
            strengths.append("The answer demonstrates strong understanding of the expected content.")
        elif status == "mostly_correct":
            strengths.append("The answer shows a sound understanding of the main concept.")
        elif status == "partially_correct":
            strengths.append("The response includes some relevant understanding of the question.")
        if scores["relevance"] >= self.config.strength_threshold:
            strengths.append("The answer directly addresses the question.")
        if scores["semantic"] >= self.config.strength_threshold:
            strengths.append("The explanation is semantically consistent with the expected answer.")
        if scores["coverage"] >= self.config.strength_threshold:
            strengths.append("The answer covers most of the important concepts.")
        if scores["completeness"] >= self.config.strength_threshold:
            strengths.append("The answer provides a sufficiently complete explanation.")
        return self._unique(strengths)

    def _missing_concepts(self, coverage: float | None) -> list[str]:
        if coverage is not None and coverage < self.config.weakness_threshold:
            return ["Some important expected concepts are missing."]
        return []

    def _weak_areas(self, scores: dict[str, float | None], status: str) -> list[str]:
        weak_areas: list[str] = []
        if scores["relevance"] < self.config.weakness_threshold:
            weak_areas.append("The response does not fully focus on the question.")
        if scores["semantic"] < self.config.weakness_threshold:
            weak_areas.append("The response differs substantially from the expected explanation.")
        if scores["coverage"] < self.config.weakness_threshold:
            weak_areas.append("Some important concepts are not yet covered.")
        if scores["completeness"] < self.config.weakness_threshold:
            weak_areas.append("The explanation could include more supporting details.")
        if status == "irrelevant" and not weak_areas:
            weak_areas.append("The response does not adequately address the question.")
        return self._unique(weak_areas)

    def _suggestions(self, scores: dict[str, float | None], status: str, normalized_score: float | None) -> list[str]:
        suggestions: list[str] = []
        if scores["coverage"] < self.config.weakness_threshold:
            suggestions.append("Include the important concepts that are missing from the explanation.")
        if scores["completeness"] < self.config.weakness_threshold:
            suggestions.append("Provide more supporting detail to make the explanation complete.")
        if scores["relevance"] < self.config.weakness_threshold:
            suggestions.append("Focus the response more directly on the concepts requested in the question.")
        if scores["semantic"] < self.config.weakness_threshold:
            suggestions.append("Align the explanation more closely with the expected meaning.")
        if not suggestions and status == "mostly_correct":
            suggestions.append("Add a little more supporting detail to make the explanation stronger.")
        if not suggestions and self.config.score_band(normalized_score) == "good":
            suggestions.append("Add a little more detail to make the explanation even stronger.")
        return self._unique(suggestions)

    def _overall(self, status: str, normalized_score: float | None) -> str:
        score_band = self.config.score_band(normalized_score)
        if status == "correct":
            if score_band == "excellent":
                return "The answer is accurate, relevant, and well developed."
            return "The answer demonstrates strong understanding and is close to a complete explanation."
        if status == "mostly_correct":
            if score_band in {"excellent", "good"}:
                return "The answer demonstrates good understanding but could be improved with a few supporting details."
            return "The answer shows useful understanding but needs clearer support for the expected content."
        if status == "partially_correct":
            if score_band == "partial":
                return "The answer includes some relevant ideas but needs more complete coverage of the expected content."
            return "The answer addresses part of the question but needs more complete coverage of the expected content."
        if status == "irrelevant":
            if score_band == "minimal":
                return "The response received very limited credit because it does not focus enough on the expected concepts."
            if score_band == "low":
                return "The response has limited relevant content and should focus more closely on the expected concepts."
            return "The response needs to focus more closely on the concepts requested in the question."
        return "The response would benefit from a clearer and more complete explanation."

    @staticmethod
    def _normalized_score(marks: MarksResult) -> float | None:
        if marks.marks_awarded is None or marks.max_marks is None:
            return None
        if marks.max_marks <= 0:
            raise ValueError("Maximum marks must be positive when marks are awarded")
        return marks.marks_awarded / marks.max_marks

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))
