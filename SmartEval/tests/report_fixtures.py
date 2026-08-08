from domain.entities.evaluation_item import EvaluationItem
from domain.entities.evaluation_report import EvaluationReport
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.feedback_result import FeedbackResult
from domain.entities.marks_result import MarksResult
from domain.entities.model_answer import ModelAnswer
from domain.entities.question import Question
from domain.entities.student_answer import StudentAnswer
from domain.entities.total_marks_result import TotalMarksResult
from domain.value_objects.question_id import QuestionId
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from reporting.evaluation_report_generator import EvaluationReportGenerator


def report_inputs() -> tuple[
    list[EvaluationItem],
    list[EvaluationResult],
    list[MarksResult],
    list[FeedbackResult],
    TotalMarksResult,
]:
    specifications = [
        ("correct", .95, 10.0, "A complete answer."),
        ("mostly_correct", .75, 8.0, "A mostly complete answer."),
        ("partially_correct", .5, 5.0, "A partial answer."),
        ("no_answer", 0.0, 0.0, ""),
        ("model_answer_missing", None, None, "An answer without a model answer."),
    ]
    items: list[EvaluationItem] = []
    evaluations: list[EvaluationResult] = []
    marks_results: list[MarksResult] = []
    feedback_results: list[FeedbackResult] = []
    for number, (status, score, awarded, student_text) in enumerate(specifications, start=1):
        question_id = QuestionId(number)
        question = Question(question_id, number, f"Question {number}", 10)
        model = None if status == "model_answer_missing" else ModelAnswer(question_id, f"Expected answer {number}.")
        student = StudentAnswer(question_id, student_text)
        items.append(EvaluationItem(question, model, student))
        evaluations.append(EvaluationResult(question_id, score, score, score, score, status, "test"))
        percentage = None if awarded is None else awarded * 10
        marks_results.append(MarksResult(question_id, 10, awarded, percentage, status))
        feedback_results.append(FeedbackResult(
            question_id=question_id,
            marks_awarded=awarded,
            max_marks=10,
            status=status,
            strengths=("The answer directly addresses the question.",) if status in {"correct", "mostly_correct"} else (),
            missing_concepts=("Some important expected concepts are missing.",) if status == "partially_correct" else (),
            weak_areas=("The explanation could include more supporting details.",) if status == "partially_correct" else (),
            improvement_suggestions=("Provide more supporting detail to make the explanation complete.",) if status == "partially_correct" else (),
            overall_feedback=f"Feedback for question {number}.",
        ))
    total = TotalMarksCalculator(RoundingPolicy(1)).calculate(marks_results)
    return items, evaluations, marks_results, feedback_results, total


def build_report() -> EvaluationReport:
    return EvaluationReportGenerator().generate(*report_inputs(), report_id="evaluation_test")
