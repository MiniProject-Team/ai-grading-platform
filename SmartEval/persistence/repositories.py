from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .models import EvaluationQuestionRecord, EvaluationRecord, ExamRecord, StudentRecord


class StudentRepository(ABC):
    @abstractmethod
    def get_or_create(self, student_id: str, *, name: str | None, roll_number: str | None) -> StudentRecord: ...


class ExamRepository(ABC):
    @abstractmethod
    def get_or_create(self, exam_id: str, *, name: str | None, subject: str | None, semester: str | None, exam_date: str | None) -> ExamRecord: ...


class EvaluationRepository(ABC):
    @abstractmethod
    def get(self, evaluation_id: str) -> EvaluationRecord | None: ...

    @abstractmethod
    def add(self, record: EvaluationRecord) -> None: ...

    @abstractmethod
    def list(self, *, page: int, page_size: int, student_id: str | None = None, exam_id: str | None = None, status: str | None = None) -> tuple[list[EvaluationRecord], int]: ...


class EvaluationQuestionRepository(ABC):
    @abstractmethod
    def add_all(self, records: list[EvaluationQuestionRecord]) -> None: ...


class SQLAlchemyStudentRepository(StudentRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, student_id: str, *, name: str | None, roll_number: str | None) -> StudentRecord:
        record = self.session.scalar(select(StudentRecord).where(StudentRecord.student_id == student_id))
        if record is None:
            record = StudentRecord(student_id=student_id, name=name, roll_number=roll_number)
            self.session.add(record)
        else:
            record.name = name or record.name
            record.roll_number = roll_number or record.roll_number
        return record


class SQLAlchemyExamRepository(ExamRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, exam_id: str, *, name: str | None, subject: str | None, semester: str | None, exam_date: str | None) -> ExamRecord:
        record = self.session.scalar(select(ExamRecord).where(ExamRecord.exam_id == exam_id))
        if record is None:
            record = ExamRecord(exam_id=exam_id, name=name, subject=subject, semester=semester, exam_date=exam_date)
            self.session.add(record)
        else:
            record.name = name or record.name
            record.subject = subject or record.subject
            record.semester = semester or record.semester
            record.exam_date = exam_date or record.exam_date
        return record


class SQLAlchemyEvaluationRepository(EvaluationRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, evaluation_id: str) -> EvaluationRecord | None:
        return self.session.scalar(
            select(EvaluationRecord)
            .options(selectinload(EvaluationRecord.questions))
            .where(EvaluationRecord.evaluation_id == evaluation_id),
        )

    def add(self, record: EvaluationRecord) -> None:
        self.session.add(record)

    def list(self, *, page: int, page_size: int, student_id: str | None = None, exam_id: str | None = None, status: str | None = None) -> tuple[list[EvaluationRecord], int]:
        statement = select(EvaluationRecord).options(selectinload(EvaluationRecord.questions)).order_by(EvaluationRecord.created_at.desc())
        count_statement = select(func.count()).select_from(EvaluationRecord)
        if student_id:
            statement = statement.join(EvaluationRecord.student).where(StudentRecord.student_id == student_id)
            count_statement = count_statement.join(EvaluationRecord.student).where(StudentRecord.student_id == student_id)
        if exam_id:
            statement = statement.join(EvaluationRecord.exam).where(ExamRecord.exam_id == exam_id)
            count_statement = count_statement.join(EvaluationRecord.exam).where(ExamRecord.exam_id == exam_id)
        if status:
            statement = statement.where(EvaluationRecord.status == status)
            count_statement = count_statement.where(EvaluationRecord.status == status)
        total = self.session.scalar(count_statement) or 0
        records = list(self.session.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
        return records, total


class SQLAlchemyEvaluationQuestionRepository(EvaluationQuestionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_all(self, records: list[EvaluationQuestionRecord]) -> None:
        self.session.add_all(records)
