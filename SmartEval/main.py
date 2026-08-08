from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.input_pipeline import InputPipeline
from app.evaluation_pipeline import EvaluationPipeline
from app.feedback_pipeline import FeedbackPipeline
from app.marks_pipeline import MarksPipeline
from app.report_pipeline import ReportPipeline
from config.settings import Settings
from evaluation.factory import build_evaluation_engine
from evaluation.marks.factory import build_marks_calculator
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from feedback.factory import build_feedback_service
from integration.evaluation_service import EvaluationRequest, EvaluationService
from reporting.evaluation_report_generator import EvaluationReportGenerator
from reporting.json_report_exporter import JsonReportExporter
from reporting.text_report_exporter import TextReportExporter
from utils.logger import configure_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="SmartEval input, semantic evaluation, marks, and feedback analysis.")
    parser.add_argument("--question-paper", required=True, type=Path)
    parser.add_argument("--model-answer", required=True, type=Path)
    parser.add_argument("--student-text", type=Path, help="Existing OCR text for Phases 4-8")
    parser.add_argument("--student-sheet", type=Path, help="Full-page PDF or image to recognize through SmartHTR")
    parser.add_argument("--evaluate", action="store_true", help="Run Phase 5 semantic signals without calculating marks")
    parser.add_argument("--marks", action="store_true", help="Run Phases 5 and 6, including configurable marks calculation")
    parser.add_argument("--feedback", action="store_true", help="Run Phases 5-7, including teacher-style feedback")
    parser.add_argument("--report", action="store_true", help="Run Phases 5-8 and export JSON and text reports")
    parser.add_argument("--report-id", help="Optional identifier for the generated report")
    parser.add_argument("--student-id")
    parser.add_argument("--student-name")
    parser.add_argument("--roll-number")
    parser.add_argument("--subject")
    parser.add_argument("--exam-name")
    parser.add_argument("--semester")
    parser.add_argument("--debug", action="store_true", help="Print concise pipeline diagnostics without OCR text")
    args = parser.parse_args()

    settings = Settings.from_environment()
    logger = configure_logging(settings)
    if args.student_sheet and args.student_text:
        parser.error("Use either --student-sheet or --student-text, not both.")
    if args.student_sheet:
        execution = EvaluationService(settings).evaluate_and_export(EvaluationRequest(
            question_paper_path=args.question_paper,
            model_answer_path=args.model_answer,
            student_answer_sheet_path=args.student_sheet,
            student_id=args.student_id,
            student_name=args.student_name,
            roll_number=args.roll_number,
            subject=args.subject,
            exam_name=args.exam_name,
            semester=args.semester,
            report_id=args.report_id,
        ))
        report = execution.report
        print("SMART EVAL")
        print(f"OCR: {execution.ocr_result.status.upper() if execution.ocr_result else 'FAILED'}")
        print(f"Questions: {report.summary.total_questions}")
        print(f"Evaluated: {report.summary.evaluated_questions}")
        print(f"Marks: {report.summary.awarded_marks} / {report.summary.evaluated_maximum_marks}")
        print(f"Percentage: {'Unavailable' if report.summary.percentage is None else f'{report.summary.percentage}%'}")
        print(f"Status: {report.status.upper()}")
        print(f"Report: {execution.json_report_path}")
        if args.debug:
            ocr = execution.ocr_result
            print("\nDiagnostics:")
            print(f"OCR pages: {len(ocr.pages) if ocr else 0}")
            print(f"OCR text length: {len(ocr.full_text) if ocr else 0}")
            print(f"Model answers: {sum(result.model_answer is not None for result in report.question_results)}")
            print(f"Student answers: {sum(bool(result.student_answer.strip()) for result in report.question_results)}")
            print(f"Mapping: {'OK' if report.status != 'failed' else 'FAILED'}")
            print(f"Report status: {report.status}")
        return 0 if report.status != "failed" else 1
    if args.student_text is None:
        parser.error("--student-text is required unless --student-sheet is provided.")
    try:
        input_pipeline = InputPipeline(settings)
        if args.report:
            feedback_pipeline = FeedbackPipeline(
                EvaluationPipeline(input_pipeline, build_evaluation_engine(settings)),
                build_marks_calculator(settings),
                TotalMarksCalculator(RoundingPolicy(settings.marks_decimal_places)),
                build_feedback_service(settings),
            )
            report = ReportPipeline(feedback_pipeline, EvaluationReportGenerator()).run(
                args.question_paper, args.model_answer, args.student_text,
                report_id=args.report_id,
            )
            json_path = JsonReportExporter(settings.reports_directory).export(report)
            text_path = TextReportExporter(settings.reports_directory).export(report)
            results, marks_results, total_marks, feedback_results = [], [], None, []
        elif args.feedback:
            feedback_pipeline = FeedbackPipeline(
                EvaluationPipeline(input_pipeline, build_evaluation_engine(settings)),
                build_marks_calculator(settings),
                TotalMarksCalculator(RoundingPolicy(settings.marks_decimal_places)),
                build_feedback_service(settings),
            )
            analysis, results, marks_results, total_marks, feedback_results = feedback_pipeline.run(
                args.question_paper, args.model_answer, args.student_text,
            )
        elif args.marks:
            marks_pipeline = MarksPipeline(
                EvaluationPipeline(input_pipeline, build_evaluation_engine(settings)),
                build_marks_calculator(settings),
                TotalMarksCalculator(RoundingPolicy(settings.marks_decimal_places)),
            )
            analysis, marks_results, total_marks = marks_pipeline.run(args.question_paper, args.model_answer, args.student_text)
            results, feedback_results = [], []
        elif args.evaluate:
            analysis, results = EvaluationPipeline(input_pipeline, build_evaluation_engine(settings)).run(args.question_paper, args.model_answer, args.student_text)
            marks_results, total_marks, feedback_results = [], None, []
        else:
            analysis = input_pipeline.run(args.question_paper, args.model_answer, args.student_text)
            results, marks_results, total_marks, feedback_results = [], [], None, []
    except Exception as error:
        logger.exception("SmartEval input analysis failed")
        print(f"Input analysis failed: {error}", file=sys.stderr)
        return 1

    if args.report:
        print("SMART EVAL EVALUATION REPORT")
        print(f"Report ID: {report.report_id}")
        print(f"Status: {report.status}")
        print(f"Total: {report.summary.awarded_marks}/{report.summary.evaluated_maximum_marks} ({report.summary.percentage}%)")
        print(f"JSON: {json_path}")
        print(f"Text: {text_path}")
        return 0

    print("SMART EVAL INPUT ANALYSIS")
    print(f"Questions found: {len(analysis.questions)}")
    print(f"Model answers found: {len(analysis.model_answers)}")
    print(f"Student answers found: {len(analysis.student_answers)}")
    print("\nMapping:")
    for item in analysis.items:
        status = "OK" if not item.model_answer_missing and not item.student_answer_missing else "MISSING INPUT"
        print(f"{item.question.question_id}: {status}")
    if results:
        print("\nEvaluation signals:")
        for result in results:
            print(f"{result.question_id}: {result.status} (semantic={result.semantic_similarity}, coverage={result.concept_coverage}, relevance={result.relevance}, completeness={result.completeness})")
    if marks_results:
        print("\nMarks:")
        for result in marks_results:
            print(f"{result.question_id}: {result.marks_awarded}/{result.max_marks} ({result.evaluation_status})")
        print(f"Total: {total_marks.awarded_marks}/{total_marks.evaluated_maximum_marks} ({total_marks.percentage}%)")
        if total_marks.unevaluated_questions:
            print("Unevaluated: " + ", ".join(str(question_id) for question_id in total_marks.unevaluated_questions))
    if feedback_results:
        print("\nFeedback:")
        for result in feedback_results:
            print(f"{result.question_id}: {result.overall_feedback}")
            for suggestion in result.improvement_suggestions:
                print(f"  Suggestion: {suggestion}")
    elif results:
        print("\nSemantic evaluation completed. No marks or feedback were calculated.")
    else:
        print("\nInput validation successful. No semantic grading or marks were calculated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
