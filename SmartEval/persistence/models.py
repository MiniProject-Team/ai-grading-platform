from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> UUID:
    return uuid4()


class StudentRecord(Base):
    __tablename__ = "students"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    roll_number: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    evaluations: Mapped[list[EvaluationRecord]] = relationship(back_populates="student")


class ExamRecord(Base):
    __tablename__ = "exams"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_uuid)
    exam_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    subject: Mapped[str | None] = mapped_column(String(256))
    semester: Mapped[str | None] = mapped_column(String(128))
    exam_date: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    evaluations: Mapped[list[EvaluationRecord]] = relationship(back_populates="exam")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_uuid)
    evaluation_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    student_id: Mapped[UUID | None] = mapped_column(ForeignKey("students.id"), index=True)
    exam_id: Mapped[UUID | None] = mapped_column(ForeignKey("exams.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    awarded_marks: Mapped[float] = mapped_column(Float, nullable=False)
    evaluated_maximum_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_maximum_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[float | None] = mapped_column(Float)
    error_summary: Mapped[str | None] = mapped_column(Text)
    question_paper_filename: Mapped[str | None] = mapped_column(String(512))
    model_answer_filename: Mapped[str | None] = mapped_column(String(512))
    student_answer_filename: Mapped[str | None] = mapped_column(String(512))
    report_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    evaluation_metadata: Mapped[dict[str, str]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student: Mapped[StudentRecord | None] = relationship(back_populates="evaluations")
    exam: Mapped[ExamRecord | None] = relationship(back_populates="evaluations")
    questions: Mapped[list[EvaluationQuestionRecord]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan", order_by="EvaluationQuestionRecord.question_number",
    )

    __table_args__ = (Index("ix_evaluations_status_created_at", "status", "created_at"),)


class EvaluationQuestionRecord(Base):
    __tablename__ = "evaluation_questions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_uuid)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(128), nullable=False)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    max_marks: Mapped[int | None] = mapped_column(Integer)
    alternative_group: Mapped[str | None] = mapped_column(String(64))
    awarded_marks: Mapped[float | None] = mapped_column(Float)
    percentage: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    semantic_similarity: Mapped[float | None] = mapped_column(Float)
    concept_coverage: Mapped[float | None] = mapped_column(Float)
    relevance: Mapped[float | None] = mapped_column(Float)
    completeness: Mapped[float | None] = mapped_column(Float)
    student_answer: Mapped[str | None] = mapped_column(Text)
    model_answer: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_concepts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    weak_areas: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    improvement_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    overall_feedback: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation: Mapped[EvaluationRecord] = relationship(back_populates="questions")

    __table_args__ = (
        UniqueConstraint("evaluation_id", "question_id", name="uq_evaluation_question_id"),
        CheckConstraint("semantic_similarity IS NULL OR (semantic_similarity >= 0.0 AND semantic_similarity <= 1.0)", name="ck_semantic_similarity_range"),
        CheckConstraint("concept_coverage IS NULL OR (concept_coverage >= 0.0 AND concept_coverage <= 1.0)", name="ck_concept_coverage_range"),
        CheckConstraint("relevance IS NULL OR (relevance >= 0.0 AND relevance <= 1.0)", name="ck_relevance_range"),
        CheckConstraint("completeness IS NULL OR (completeness >= 0.0 AND completeness <= 1.0)", name="ck_completeness_range"),
        Index("ix_evaluation_questions_evaluation_number", "evaluation_id", "question_number"),
    )
