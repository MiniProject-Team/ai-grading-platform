from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.settings import Settings
from domain.entities.evaluation_report import EvaluationReport
from reporting.report_validator import ReportValidator

from .models import EvaluationQuestionRecord, EvaluationRecord
from .repositories import (
    SQLAlchemyEvaluationQuestionRepository,
    SQLAlchemyEvaluationRepository,
    SQLAlchemyExamRepository,
    SQLAlchemyStudentRepository,
)


class PersistenceError(RuntimeError):
    """Raised when an evaluation cannot be durably stored or retrieved."""


@dataclass(frozen=True, slots=True)
class PersistedEvaluation:
    evaluation_id: str
    status: str
    report_payload: dict[str, object]
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationPage:
    items: tuple[PersistedEvaluation, ...]
    total: int
    page: int
    page_size: int


class EvaluationPersistenceService:
    """Persists immutable report snapshots and queryable evaluation facts atomically."""

    def __init__(self, session_factory: Callable[[], Session], settings: Settings) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._validator = ReportValidator()
        self._logger = logging.getLogger("smarteval")

    def persist(
        self,
        report: EvaluationReport,
        *,
        question_paper_filename: str | None = None,
        model_answer_filename: str | None = None,
        student_answer_filename: str | None = None,
    ) -> PersistedEvaluation:
        self._validator.validate(report)
        self._logger.info("Evaluation persistence started: %s", report.report_id)
        session = self._session_factory()
        try:
            with session.begin():
                evaluations = SQLAlchemyEvaluationRepository(session)
                existing = evaluations.get(report.report_id)
                if existing is not None:
                    return self._snapshot(existing)

                student = None
                student_info = report.student_information
                if student_info and student_info.student_id:
                    student = SQLAlchemyStudentRepository(session).get_or_create(
                        student_info.student_id,
                        name=student_info.student_name,
                        roll_number=student_info.roll_number,
                    )

                exam = None
                exam_info = report.exam_information
                if exam_info and exam_info.exam_id:
                    exam = SQLAlchemyExamRepository(session).get_or_create(
                        exam_info.exam_id,
                        name=exam_info.exam_name,
                        subject=exam_info.subject,
                        semester=exam_info.semester,
                        exam_date=exam_info.exam_date,
                    )

                payload = self._report_payload(report)
                record = EvaluationRecord(
                    evaluation_id=report.report_id,
                    student=student,
                    exam=exam,
                    status=report.status,
                    awarded_marks=report.summary.awarded_marks,
                    evaluated_maximum_marks=report.summary.evaluated_maximum_marks,
                    exam_maximum_marks=report.summary.exam_maximum_marks,
                    percentage=report.summary.percentage,
                    error_summary="; ".join(report.warnings) if report.warnings else None,
                    question_paper_filename=question_paper_filename,
                    model_answer_filename=model_answer_filename,
                    student_answer_filename=student_answer_filename,
                    report_payload=payload,
                    evaluation_metadata=report.metadata,
                )
                evaluations.add(record)
                questions = [self._question_record(record, number, result.to_dict()) for number, result in enumerate(report.question_results, start=1)]
                SQLAlchemyEvaluationQuestionRepository(session).add_all(questions)
                session.flush()
                self._logger.info("Evaluation persisted: %s", report.report_id)
                return PersistedEvaluation(report.report_id, report.status, payload)
        except SQLAlchemyError as error:
            self._logger.exception("Evaluation persistence failed: %s", report.report_id)
            raise PersistenceError("Evaluation persistence is unavailable.") from error
        finally:
            session.close()

    def get(self, evaluation_id: str) -> PersistedEvaluation | None:
        session = self._session_factory()
        try:
            record = SQLAlchemyEvaluationRepository(session).get(evaluation_id)
            return self._snapshot(record) if record else None
        except SQLAlchemyError as error:
            self._logger.exception("Evaluation retrieval failed: %s", evaluation_id)
            raise PersistenceError("Evaluation history is unavailable.") from error
        finally:
            session.close()

    def list(self, *, page: int, page_size: int, student_id: str | None = None, exam_id: str | None = None, status: str | None = None) -> EvaluationPage:
        session = self._session_factory()
        try:
            records, total = SQLAlchemyEvaluationRepository(session).list(
                page=page, page_size=page_size, student_id=student_id, exam_id=exam_id, status=status,
            )
            return EvaluationPage(tuple(self._snapshot(record) for record in records), total, page, page_size)
        except SQLAlchemyError as error:
            self._logger.exception("Evaluation history lookup failed")
            raise PersistenceError("Evaluation history is unavailable.") from error
        finally:
            session.close()

    def _question_record(self, evaluation: EvaluationRecord, question_number: int, result: dict[str, object]) -> EvaluationQuestionRecord:
        evaluation_data = result["evaluation"]
        marks = result["marks"]
        feedback = result["feedback"]
        assert isinstance(evaluation_data, dict) and isinstance(marks, dict) and isinstance(feedback, dict)
        retain_content = self._settings.retain_evaluation_content
        return EvaluationQuestionRecord(
            evaluation=evaluation,
            question_id=str(result["question_id"]),
            question_number=question_number,
            question_text=str(result["question"]),
            max_marks=result["max_marks"],
            awarded_marks=marks["awarded"],
            percentage=marks["percentage"],
            status=str(evaluation_data["status"]),
            semantic_similarity=evaluation_data["semantic_similarity"],
            concept_coverage=evaluation_data["concept_coverage"],
            relevance=evaluation_data["relevance"],
            completeness=evaluation_data["completeness"],
            student_answer=str(result["student_answer"]) if retain_content else None,
            model_answer=str(result["model_answer"]) if retain_content and result["model_answer"] is not None else None,
            strengths=list(feedback["strengths"]),
            missing_concepts=list(feedback["missing_concepts"]),
            weak_areas=list(feedback["weak_areas"]),
            improvement_suggestions=list(feedback["improvement_suggestions"]),
            overall_feedback=str(feedback["overall_feedback"]),
        )

    @staticmethod
    def _snapshot(record: EvaluationRecord) -> PersistedEvaluation:
        created_at = record.created_at.isoformat() if record.created_at else None
        return PersistedEvaluation(record.evaluation_id, record.status, dict(record.report_payload), created_at)

    def _report_payload(self, report: EvaluationReport) -> dict[str, object]:
        payload = report.to_dict()
        if self._settings.retain_evaluation_content:
            return payload
        for result in payload["question_results"]:
            assert isinstance(result, dict)
            result["student_answer"] = ""
            result["model_answer"] = None
        return payload
