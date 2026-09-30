"""Paper denominators based on explicit parsed OR membership."""
from collections import defaultdict
from typing import Iterable, Protocol

from domain.value_objects.question_id import QuestionId


class MarkedQuestion(Protocol):
    question_id: QuestionId
    max_marks: int | None


def calculate_effective_max_marks(questions: Iterable[MarkedQuestion]) -> int:
    """Sum compulsory rows and the largest parent alternative in each OR group.

    Parent numbers identify sides only within an explicit alternative_group;
    question numbering never establishes an OR relationship by itself.
    Missing marks retain the existing zero contribution behavior.
    """
    groups: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    consumed: set[QuestionId] = set()
    compulsory = 0
    for question in questions:
        if question.question_id in consumed:
            raise ValueError(f"Duplicate question ID: {question.question_id}")
        consumed.add(question.question_id)
        marks = question.max_marks or 0
        group = getattr(question, "alternative_group", None)
        if group is None:
            compulsory += marks
        else:
            groups[group][question.question_id.number] += marks
    return compulsory + sum(max(alternatives.values()) for alternatives in groups.values())
