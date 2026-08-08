from __future__ import annotations

import logging
import time
from pathlib import Path

from services.student_text_provider import StudentTextProvider

from .smarthtr_client import (
    SmartHTROCRResult,
    SmartHTRClientError,
)


class StudentTextExtractionError(RuntimeError):
    pass


class EmptyOCRResultError(StudentTextExtractionError):
    pass


class SmartHTRIntegrationService:
    _SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

    def __init__(self, client) -> None:
        self.client = client
        self.logger = logging.getLogger("smarteval")

    def extract(self, student_sheet: Path) -> SmartHTROCRResult:
        student_sheet = student_sheet.resolve()
        if not student_sheet.is_file():
            raise StudentTextExtractionError("Student answer sheet was not found.")
        if student_sheet.suffix.lower() not in self._SUPPORTED_SUFFIXES:
            raise StudentTextExtractionError(f"Unsupported student answer-sheet format: {student_sheet.suffix}")
        started = time.perf_counter()
        self.logger.info("SmartHTR document processing started: file_size=%s", student_sheet.stat().st_size)
        try:
            result = self.client.recognize(student_sheet)
        except SmartHTRClientError as error:
            raise StudentTextExtractionError(str(error)) from error
        except Exception as error:
            raise StudentTextExtractionError("Student handwritten text extraction failed.") from error
        if result.status not in {"success", "partially_processed"}:
            raise StudentTextExtractionError("Student handwritten text extraction failed.")
        if not result.full_text.strip():
            raise EmptyOCRResultError("No handwritten text was extracted from the student answer sheet.")
        self.logger.info(
            "SmartHTR document processing completed: status=%s pages=%s text_length=%s duration=%.2fs warnings=%s",
            result.status,
            len(result.pages),
            len(result.full_text),
            time.perf_counter() - started,
            len(result.warnings),
        )
        return result


class SmartHTRStudentTextProvider(StudentTextProvider):
    """Provides ordered full-page SmartHTR text to existing SmartEval input handling."""

    def __init__(self, integration_service: SmartHTRIntegrationService, continue_on_partial: bool = True) -> None:
        self.integration_service = integration_service
        self.continue_on_partial = continue_on_partial
        self.last_result: SmartHTROCRResult | None = None

    def get_text(self, source: Path) -> str:
        self.last_result = self.integration_service.extract(source)
        if self.last_result.status == "partially_processed" and not self.continue_on_partial:
            raise StudentTextExtractionError("Student handwritten text extraction was only partially processed.")
        return self.last_result.full_text


class SharedRuntimeSmartHTRStudentTextProvider(SmartHTRStudentTextProvider):
    """Provides SmartHTR text from the current Python runtime to SmartEval."""
