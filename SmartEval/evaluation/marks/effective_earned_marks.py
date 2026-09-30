"""Select whole OR alternatives; retain every individual evaluation."""
from dataclasses import dataclass
from decimal import Decimal

from domain.entities.marks_result import MarksResult
from .effective_max_marks import MarkedQuestion


@dataclass(frozen=True)
class EarnedAggregation:
    earned: float
    or_groups: dict[str, dict]


def calculate_effective_earned_marks(
    results: list[MarksResult], questions: list[MarkedQuestion],
) -> EarnedAggregation:
    """First alternative in paper order wins exact ties.

    OR scores use stored weighted contributions before display rounding when
    available. Unknown/unanswered rows contribute zero, retaining their status.
    Compulsory rows retain their existing awarded marks. No totals are clamped.
    """
    indexed = {r.question_id: r for r in results}
    if len(indexed) != len(results):
        raise ValueError("Duplicate marks result IDs")
    if {q.question_id for q in questions} != set(indexed):
        raise ValueError("Question and marks result IDs must match")
    consumed = set()
    groups = {}
    compulsory = Decimal(0)
    for question in questions:
        identifier = question.question_id
        if identifier in consumed:
            raise ValueError(f"Duplicate question ID: {identifier}")
        consumed.add(identifier)
        result = indexed[identifier]
        group = getattr(question, 'alternative_group', None)
        earned = Decimal(str(result.marks_awarded or 0)) if result.max_marks is not None else Decimal(0)
        if group is None:
            compulsory += earned
            continue
        if result.marks_awarded is not None and result.max_marks is not None and result.breakdown and result.evaluation_status != 'no_answer':
            earned = sum((Decimal(str(c.contribution)) for c in result.breakdown.values()), Decimal(0)) * result.max_marks
        alternative = groups.setdefault(group, {}).setdefault(
            f'Q{identifier.number}', {'earned': Decimal(0), 'maximum': 0},
        )
        alternative['earned'] += earned
        alternative['maximum'] += question.max_marks or 0
    if consumed != set(indexed):
        raise ValueError("Question and marks result IDs must match")
    total = compulsory
    selections = {}
    for group, alternatives in groups.items():
        selected = max(alternatives, key=lambda name: alternatives[name]['earned'])
        earned = alternatives[selected]['earned']
        total += earned
        selections[group] = {
            'alternatives': [dict(question_group=name, earned=float(values['earned']),
                                  maximum=values['maximum'], counted=name == selected)
                             for name, values in alternatives.items()],
            'selected_alternative': selected,
            'counted_earned': float(earned),
            'effective_maximum': max(values['maximum'] for values in alternatives.values()),
        }
    return EarnedAggregation(float(total), selections)
