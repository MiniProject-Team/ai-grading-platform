from __future__ import annotations

import logging
import time
from pathlib import Path

from services.student_text_provider import StudentTextProvider
from app.progress import report_progress

from .ocr_service import OCRResult
from .smarthtr_client import SmartHTRClientError


class StudentTextExtractionError(RuntimeError):
    pass


class EmptyOCRResultError(StudentTextExtractionError):
    pass


class SmartHTRIntegrationService:
    _SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

    def __init__(self, client) -> None:
        self.client = client
        self.logger = logging.getLogger("smarteval")
        self.last_result: OCRResult | None = None
        self.last_raw_ocr_debug_path: Path | None = None

    def extract(self, student_sheet: Path) -> OCRResult:
        student_sheet = student_sheet.resolve()
        if not student_sheet.is_file():
            raise StudentTextExtractionError("Student answer sheet was not found.")
        if student_sheet.suffix.lower() not in self._SUPPORTED_SUFFIXES:
            raise StudentTextExtractionError(f"Unsupported student answer-sheet format: {student_sheet.suffix}")
        started = time.perf_counter()
        self.logger.info("SmartHTR document processing started: file_size=%s", student_sheet.stat().st_size)
        try:
            result = self.client.recognize(student_sheet)
            self.last_result = result
        except SmartHTRClientError as error:
            raise StudentTextExtractionError(str(error)) from error
        except Exception as error:
            raise StudentTextExtractionError("Student handwritten text extraction failed.") from error
        self._log_raw_ocr_diagnostics(result)
        if result.status not in {"success", "partially_processed"} or not result.success:
            message = result.error or "Student handwritten text extraction failed."
            raise StudentTextExtractionError(message)
        if not result.full_text.strip():
            raise EmptyOCRResultError("No handwritten text was extracted from the student answer sheet.")
        self.logger.info(
            "[OCR] Provider=%s status=%s pages=%s text_length=%s duration=%.2fs warnings=%s",
            result.provider,
            result.status,
            result.pages_processed,
            len(result.full_text),
            time.perf_counter() - started,
            len(result.warnings),
        )
        report_progress("reading", f"Handwriting recognition complete: {result.pages_processed} pages, {len(result.full_text):,} characters extracted.")
        return result

    def _log_raw_ocr_diagnostics(self, result: OCRResult) -> None:
        self.logger.info("[OCR DEBUG] Provider: %s", result.provider)
        self.logger.info("[OCR DEBUG] Status: %s", result.status)
        self.logger.info("[OCR DEBUG] Page count: %s", result.pages_processed)
        self.logger.info("[OCR DEBUG] Total text length: %s", len(result.full_text))
        self.logger.info("[OCR DEBUG] Raw OCR first 2000 characters:\n%s", result.full_text[:2000])
        for page in result.pages:
            self.logger.info(
                "[OCR DEBUG] Page %s text length=%s first 500 characters:\n%s",
                page.page_number,
                len(page.text),
                page.text[:500],
            )

        debug_directory = Path(__file__).resolve().parents[1] / "outputs" / "debug"
        if not debug_directory.is_dir():
            self.last_raw_ocr_debug_path = None
            self.logger.warning("[OCR DEBUG] Raw OCR debug directory does not exist: %s", debug_directory)
            return
        debug_path = debug_directory / "latest_raw_ocr.txt"
        debug_path.write_text(result.full_text, encoding="utf-8")
        self.last_raw_ocr_debug_path = debug_path
        self.logger.info("[OCR DEBUG] Complete raw OCR saved to: %s", debug_path)


class SmartHTRStudentTextProvider(StudentTextProvider):
    """Provides ordered full-page SmartHTR text to existing SmartEval input handling."""

    def __init__(self, integration_service: SmartHTRIntegrationService, continue_on_partial: bool = True) -> None:
        self.integration_service = integration_service
        self.continue_on_partial = continue_on_partial
        self.last_result: OCRResult | None = None

    def get_text(self, source: Path) -> str:
        try:
            self.last_result = self.integration_service.extract(source)
        except StudentTextExtractionError:
            self.last_result = self.integration_service.last_result
            raise
        if self.last_result.status == "partially_processed" and not self.continue_on_partial:
            raise StudentTextExtractionError("Student handwritten text extraction was only partially processed.")
        return self.last_result.full_text


class SharedRuntimeSmartHTRStudentTextProvider(SmartHTRStudentTextProvider):
    """Provides SmartHTR text from the current Python runtime to SmartEval."""
