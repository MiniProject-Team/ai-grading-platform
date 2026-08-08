from __future__ import annotations

from dataclasses import dataclass, field

from domain.value_objects.question_id import QuestionId

from .evaluation_result import EvaluationResult
from .feedback_result import FeedbackResult
from .marks_result import MarksResult


@dataclass(frozen=True, slots=True)
class StudentInformation:
    student_id: str | None = None
    student_name: str | None = None
    roll_number: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {key: value for key, value in {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "roll_number": self.roll_number,
        }.items() if value is not None}


@dataclass(frozen=True, slots=True)
class ExamInformation:
    exam_name: str | None = None
    subject: str | None = None
    semester: str | None = None
    exam_date: str | None = None
    total_questions: int | None = None
    exam_id: str | None = None

    def to_dict(self) -> dict[str, str | int]:
        return {key: value for key, value in {
            "exam_name": self.exam_name,
            "subject": self.subject,
            "semester": self.semester,
            "exam_date": self.exam_date,
            "total_questions": self.total_questions,
            "exam_id": self.exam_id,
        }.items() if value is not None}


@dataclass(frozen=True, slots=True)
class QuestionEvaluationResult:
    question_id: QuestionId
    question_text: str
    max_marks: int | None
    student_answer: str
    model_answer: str | None
    evaluation: EvaluationResult
    marks: MarksResult
    feedback: FeedbackResult

    def to_dict(self) -> dict[str, object]:
        return {
            "question_id": str(self.question_id),
            "question": self.question_text,
            "max_marks": self.max_marks,
            "student_answer": self.student_answer,
            "model_answer": self.model_answer,
            "evaluation": {
                "semantic_similarity": self.evaluation.semantic_similarity,
                "concept_coverage": self.evaluation.concept_coverage,
                "relevance": self.evaluation.relevance,
                "completeness": self.evaluation.completeness,
                "status": self.evaluation.status,
                "explanation": self.evaluation.explanation,
            },
            "marks": {
                "awarded": self.marks.marks_awarded,
                "maximum": self.marks.max_marks,
                "percentage": self.marks.percentage,
                "status": self.marks.evaluation_status,
                "note": self.marks.note,
                "breakdown": {
                    name: {
                        "score": contribution.score,
                        "weight": contribution.weight,
                        "contribution": contribution.contribution,
                    }
                    for name, contribution in self.marks.breakdown.items()
                },
            },
            "feedback": {
                "strengths": list(self.feedback.strengths),
                "missing_concepts": list(self.feedback.missing_concepts),
                "weak_areas": list(self.feedback.weak_areas),
                "improvement_suggestions": list(self.feedback.improvement_suggestions),
                "overall_feedback": self.feedback.overall_feedback,
            },
        }


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    total_questions: int
    evaluated_questions: int
    unanswered_questions: int
    missing_model_answers: int
    awarded_marks: float
    evaluated_maximum_marks: int
    exam_maximum_marks: int
    percentage: float | None

    def to_dict(self) -> dict[str, int | float | None]:
        return {
            "total_questions": self.total_questions,
            "evaluated_questions": self.evaluated_questions,
            "unanswered_questions": self.unanswered_questions,
            "missing_model_answers": self.missing_model_answers,
            "awarded_marks": self.awarded_marks,
            "evaluated_maximum_marks": self.evaluated_maximum_marks,
            "exam_maximum_marks": self.exam_maximum_marks,
            "percentage": self.percentage,
        }


@dataclass(frozen=True, slots=True)
class EvaluationStatistics:
    average_semantic_similarity: float | None
    average_concept_coverage: float | None
    average_relevance: float | None
    average_completeness: float | None
    average_question_percentage: float | None
    highest_score_question: QuestionId | None
    lowest_score_question: QuestionId | None
    status_distribution: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "average_semantic_similarity": self.average_semantic_similarity,
            "average_concept_coverage": self.average_concept_coverage,
            "average_relevance": self.average_relevance,
            "average_completeness": self.average_completeness,
            "average_question_percentage": self.average_question_percentage,
            "highest_score_question": str(self.highest_score_question) if self.highest_score_question else None,
            "lowest_score_question": str(self.lowest_score_question) if self.lowest_score_question else None,
            "status_distribution": self.status_distribution,
        }


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    report_id: str
    status: str
    question_results: tuple[QuestionEvaluationResult, ...]
    summary: EvaluationSummary
    statistics: EvaluationStatistics
    warnings: tuple[str, ...] = field(default_factory=tuple)
    student_information: StudentInformation | None = None
    exam_information: ExamInformation | None = None
    top_strengths: tuple[str, ...] = field(default_factory=tuple)
    common_weaknesses: tuple[str, ...] = field(default_factory=tuple)
    overall_improvement_suggestions: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "report_id": self.report_id,
            "status": self.status,
            "student_information": self.student_information.to_dict() if self.student_information else None,
            "exam_information": self.exam_information.to_dict() if self.exam_information else None,
            "question_results": [result.to_dict() for result in self.question_results],
            "summary": self.summary.to_dict(),
            "statistics": self.statistics.to_dict(),
            "top_strengths": list(self.top_strengths),
            "common_weaknesses": list(self.common_weaknesses),
            "overall_improvement_suggestions": list(self.overall_improvement_suggestions),
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }
