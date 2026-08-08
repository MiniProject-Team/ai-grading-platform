from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from app.evaluation_pipeline import EvaluationPipeline
from app.feedback_pipeline import FeedbackPipeline
from app.input_pipeline import InputPipeline
from app.report_pipeline import ReportPipeline
from config.settings import Settings
from domain.entities.evaluation_report import EvaluationReport, ExamInformation, StudentInformation
from evaluation.factory import build_evaluation_engine
from evaluation.marks.factory import build_marks_calculator
from evaluation.marks.rounding import RoundingPolicy
from evaluation.marks.total_marks_calculator import TotalMarksCalculator
from feedback.factory import build_feedback_service
from reporting.evaluation_report_generator import EvaluationReportGenerator
from reporting.json_report_exporter import JsonReportExporter
from reporting.text_report_exporter import TextReportExporter
from services.input_manager import InputManager

from .smarthtr_client import SmartHTROCRResult, create_smarthtr_client
from .student_text_provider import (
    EmptyOCRResultError,
    SmartHTRIntegrationService,
    SharedRuntimeSmartHTRStudentTextProvider,
    SmartHTRStudentTextProvider,
    StudentTextExtractionError,
)


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    question_paper_path: Path
    model_answer_path: Path
    student_answer_sheet_path: Path
    student_id: str | None = None
    student_name: str | None = None
    roll_number: str | None = None
    subject: str | None = None
    exam_name: str | None = None
    semester: str | None = None
    exam_id: str | None = None
    exam_date: str | None = None
    report_id: str | None = None


@dataclass(frozen=True, slots=True)
class EndToEndEvaluationResult:
    report: EvaluationReport
    ocr_result: SmartHTROCRResult | None
    json_report_path: Path
    text_report_path: Path


class EvaluationService:
    """Delegate one student sheet through SmartHTR and the complete SmartEval flow."""

    _TEXT_SUFFIXES = {".txt", ".json", ".pdf"}

    def __init__(
        self,
        settings: Settings,
        *,
        student_text_provider: SmartHTRStudentTextProvider | None = None,
        report_generator: EvaluationReportGenerator | None = None,
        evaluation_engine=None,
        marks_calculator=None,
        total_calculator: TotalMarksCalculator | None = None,
        feedback_service=None,
    ) -> None:
        self.settings = settings
        self.student_text_provider = student_text_provider or SharedRuntimeSmartHTRStudentTextProvider(
            SmartHTRIntegrationService(create_smarthtr_client(settings)),
            continue_on_partial=settings.continue_on_partial_ocr,
        )
        self.report_generator = report_generator or EvaluationReportGenerator()
        self.evaluation_engine = evaluation_engine or build_evaluation_engine(settings)
        self.marks_calculator = marks_calculator or build_marks_calculator(settings)
        self.total_calculator = total_calculator or TotalMarksCalculator(RoundingPolicy(settings.marks_decimal_places))
        self.feedback_service = feedback_service or build_feedback_service(settings)
        self.logger = logging.getLogger("smarteval")

    def evaluate(self, request: EvaluationRequest) -> EvaluationReport:
        started = time.perf_counter()
        self.logger.info("End-to-end evaluation started")
        student_information, exam_information = self._metadata(request)
        try:
            self._validate_request(request)
            report = self._report_pipeline().run(
                request.question_paper_path,
                request.model_answer_path,
                request.student_answer_sheet_path,
                report_id=request.report_id,
                student_information=student_information,
                exam_information=exam_information,
                post_input_context=lambda: (self._ocr_warnings(), self._ocr_metadata()),
            )
        except EmptyOCRResultError as error:
            self.logger.warning("End-to-end evaluation stopped: OCR returned no text")
            report = self._failed_report(str(error), request, student_information, exam_information)
        except StudentTextExtractionError as error:
            self.logger.exception("SmartHTR extraction failed during end-to-end evaluation")
            report = self._failed_report(str(error), request, student_information, exam_information)
        except ValueError as error:
            self.logger.exception("Input or processing validation failed during end-to-end evaluation")
            report = self._failed_report(str(error), request, student_information, exam_information)
        except Exception:
            self.logger.exception("End-to-end evaluation failed")
            report = self._failed_report(
                "Evaluation could not be completed. Check the supplied documents and OCR text format.",
                request,
                student_information,
                exam_information,
            )
        self.logger.info("End-to-end evaluation completed with status=%s in %.2fs", report.status, time.perf_counter() - started)
        return report

    def evaluate_and_export(self, request: EvaluationRequest) -> EndToEndEvaluationResult:
        report = self.evaluate(request)
        json_path = JsonReportExporter(self.settings.reports_directory).export(report)
        text_path = TextReportExporter(self.settings.reports_directory).export(report)
        return EndToEndEvaluationResult(report, self._last_ocr_result(), json_path, text_path)

    def _report_pipeline(self) -> ReportPipeline:
        input_manager = InputManager(student_provider=self.student_text_provider)
        input_pipeline = InputPipeline(self.settings, input_manager=input_manager)
        feedback_pipeline = FeedbackPipeline(
            EvaluationPipeline(input_pipeline, self.evaluation_engine),
            self.marks_calculator,
            self.total_calculator,
            self.feedback_service,
        )
        return ReportPipeline(feedback_pipeline, self.report_generator)

    def _validate_request(self, request: EvaluationRequest) -> None:
        self._validate_text_input(request.question_paper_path, "Question paper")
        self._validate_text_input(request.model_answer_path, "Model answer")
        if not request.student_answer_sheet_path.is_file():
            raise ValueError("Student answer sheet was not found.")

    def _validate_text_input(self, path: Path, label: str) -> None:
        if not path.is_file():
            raise ValueError(f"{label} was not found.")
        if path.suffix.lower() not in self._TEXT_SUFFIXES:
            raise ValueError(f"Unsupported {label.lower()} format: {path.suffix}")

    def _ocr_warnings(self) -> tuple[str, ...]:
        result = self._last_ocr_result()
        return result.warnings if result else ()

    def _ocr_metadata(self) -> dict[str, str]:
        result = self._last_ocr_result()
        if not result:
            return {}
        return {
            "ocr_status": result.status,
            "ocr_page_count": str(len(result.pages)),
            **({"ocr_model": str(result.metadata["model"])} if result.metadata.get("model") else {}),
        }

    def _last_ocr_result(self) -> SmartHTROCRResult | None:
        return getattr(self.student_text_provider, "last_result", None)

    def _failed_report(
        self,
        message: str,
        request: EvaluationRequest,
        student_information: StudentInformation,
        exam_information: ExamInformation,
    ) -> EvaluationReport:
        return self.report_generator.failed_report(
            message,
            report_id=request.report_id,
            student_information=student_information,
            exam_information=exam_information,
            metadata=self._ocr_metadata(),
        )

    @staticmethod
    def _metadata(request: EvaluationRequest) -> tuple[StudentInformation, ExamInformation]:
        return (
            StudentInformation(request.student_id, request.student_name, request.roll_number),
            ExamInformation(
                request.exam_name,
                request.subject,
                request.semester,
                request.exam_date,
                None,
                request.exam_id,
            ),
        )
