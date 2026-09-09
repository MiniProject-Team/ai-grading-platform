"""Map parsed question, model-answer, and student-answer objects by ID."""

from __future__ import annotations

import logging

from domain.entities.evaluation_item import EvaluationItem
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer


class AnswerMappingService:
    def __init__(self) -> None:
        self.logger = logging.getLogger("smarteval")

    def map(self, questions: list[Question], model_answers: list[ModelAnswer], student_answers: list[StudentAnswer]) -> list[EvaluationItem]:
        self._validate_question_ids(questions)
        models = self._index_answers(model_answers, "model")
        students = self._index_answers(student_answers, "student")
        items = []
        for question in questions:
            model_answer = models.get(question.question_id)
            student_answer = students.get(question.question_id, StudentAnswer(question.question_id, ""))
            item = EvaluationItem(question, model_answer, student_answer)
            if item.model_answer_missing:
                self.logger.warning("Model answer unavailable for %s", question.question_id)
            if item.student_answer_missing:
                self.logger.warning("Student answer missing for %s", question.question_id)
            items.append(item)
        self._warn_unmapped_answers(models, students, {question.question_id for question in questions})
        self.logger.info("Mapping success: %s evaluation items", len(items))
        return items

    @staticmethod
    def _validate_question_ids(questions: list[Question]) -> None:
        ids = [question.question_id for question in questions]
        logging.getLogger("smarteval").info(
            "EVALUATOR INPUT DEBUG: count=%s all_ids=%s details=%s",
            len(questions), [str(item) for item in ids],
            [{"index": index, "id": str(question.question_id), "number": question.question_number,
              "text": question.question_text[:100]} for index, question in enumerate(questions)],
        )
        if len(ids) != len(set(ids)):
            first_indices: dict[object, int] = {}
            for index, question_id in enumerate(ids):
                if question_id in first_indices:
                    first, second = first_indices[question_id], index
                    raise ValueError(
                        f"Duplicate question ID: {question_id}; first evaluator object index={first} "
                        f"text={questions[first].question_text[:100]!r}; second index={second} "
                        f"text={questions[second].question_text[:100]!r}"
                    )
                first_indices[question_id] = index

    @staticmethod
    def _index_answers(answers: list[ModelAnswer] | list[StudentAnswer], label: str):
        indexed = {answer.question_id: answer for answer in answers}
        if len(indexed) != len(answers):
            raise ValueError(f"Duplicate {label} answer question IDs")
        return indexed

    def _warn_unmapped_answers(self, models, students, question_ids) -> None:
        for question_id in set(models) - question_ids:
            self.logger.warning("Model answer supplied for unknown %s", question_id)
        for question_id in set(students) - question_ids:
            self.logger.warning("Student answer supplied for unknown %s", question_id)
