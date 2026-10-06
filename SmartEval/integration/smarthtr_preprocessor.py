from __future__ import annotations

from app.progress import report_progress

import logging
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from .ocr_service import ILovePDFOCRService, OCRResult, OCRProviderError, OCRService


class SmartHTRPreprocessor:
    """Prepare a student document with SmartHTR's existing image pipeline."""

    upload_limit_bytes = 14 * 1024 * 1024
    jpeg_qualities = (85, 80, 75, 70)

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        image_dpi: int = 300,
        loader_factory: Callable[[object], object] | None = None,
        preprocessor_factory: Callable[[], object] | None = None,
        exporter_factory: Callable[[int], object] | None = None,
        enforce_upload_limit: bool = True,
    ) -> None:
        self.project_root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        self.image_dpi = image_dpi
        self.enforce_upload_limit = enforce_upload_limit
        self._loader_factory = loader_factory
        self._preprocessor_factory = preprocessor_factory
        self._exporter_factory = exporter_factory
        self.logger = logging.getLogger("smarteval")

    def preprocess(self, input_path: Path, output_directory: Path) -> Path:
        input_path = input_path.resolve()
        output_directory.mkdir(parents=True, exist_ok=True)
        self.logger.info("[OCR] Preprocessing student PDF with SmartHTR")
        report_progress("reading", "Preprocessing the student PDF to improve handwriting recognition.")
        self.logger.info("[OCR] Original PDF: %s", input_path)

        try:
            loader, image_preprocessor, exporter_factory = self._components()
            document = loader.load(input_path)
            for page in document.pages:
                image_preprocessor.process(page)

            for quality in self.jpeg_qualities:
                output_path = output_directory / f"student-preprocessed-{quality}.pdf"
                exporter_factory(quality).export(document, output_path)
                size = output_path.stat().st_size
                self.logger.info("[OCR] Preprocessed PDF: %s", output_path)
                self.logger.info("[OCR] Preprocessed PDF size: %.2f MB", size / (1024 * 1024))
                report_progress("reading", f"Student PDF preprocessing complete ({size / (1024 * 1024):.2f} MB).")
                if not self.enforce_upload_limit or size < self.upload_limit_bytes:
                    return output_path
                self.logger.warning("[OCR] Preprocessed PDF exceeds the 14 MB iLovePDF upload limit at JPEG quality %s", quality)
        except OCRProviderError:
            raise
        except Exception as error:
            raise OCRProviderError(f"SmartHTR preprocessing failed: {error}") from error

        raise OCRProviderError("SmartHTR preprocessing could not reduce the PDF below iLovePDF's 14 MB upload limit.")

    def _components(self) -> tuple[object, object, Callable[[int], object]]:
        if self._loader_factory and self._preprocessor_factory and self._exporter_factory:
            return (
                self._loader_factory(None),
                self._preprocessor_factory(),
                self._exporter_factory,
            )

        smarthtr_root = self.project_root / "SmartHTR"
        if not smarthtr_root.is_dir():
            raise OCRProviderError("The SmartHTR project directory is unavailable for PDF preprocessing.")
        if str(smarthtr_root) not in sys.path:
            sys.path.insert(0, str(smarthtr_root))
        try:
            from smarthtr.config.settings import Settings as SmartHTRSettings
            from smarthtr.document.loader import DocumentLoader
            from smarthtr.export.preprocessed_pdf_exporter import PreprocessedPdfExporter
            from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor
        except ImportError as error:
            raise OCRProviderError("SmartHTR dependencies are unavailable for PDF preprocessing.") from error

        settings = SmartHTRSettings(image_dpi=self.image_dpi)
        return DocumentLoader(settings), ImagePreprocessor(), PreprocessedPdfExporter


class PreprocessedILovePDFOCRService(ILovePDFOCRService):
    """Run SmartHTR preprocessing immediately before the existing iLovePDF flow."""

    def __init__(self, delegate: ILovePDFOCRService, preprocessor: SmartHTRPreprocessor) -> None:
        self.delegate = delegate
        self.preprocessor = preprocessor
        self.logger = logging.getLogger("smarteval")

    def recognize(self, input_path: Path) -> OCRResult:
        started = time.perf_counter()
        with TemporaryDirectory(prefix="smarteval-ilovepdf-") as directory:
            try:
                preprocessed_path = self.preprocessor.preprocess(input_path, Path(directory))
            except OCRProviderError as error:
                self.logger.exception("[OCR] Student PDF preprocessing failed")
                return self._failure(str(error), started)
            self.logger.info("[OCR] Sending preprocessed PDF to iLovePDF")
            return self.delegate.recognize(preprocessed_path)


class PreprocessedChromeOCRService(OCRService):
    """Preprocess once, retaining the PDF while the visible Chrome window uses it."""

    def __init__(self, delegate: OCRService, preprocessor: SmartHTRPreprocessor, output_directory: Path):
        self.delegate = delegate
        self.preprocessor = preprocessor
        self.output_directory = output_directory

    def recognize(self, input_path: Path) -> OCRResult:
        from uuid import uuid4
        started = time.perf_counter()
        try:
            processed = self.preprocessor.preprocess(
                input_path, self.output_directory / "chrome_ocr" / uuid4().hex,
            )
        except OCRProviderError as error:
            return OCRResult(provider="chrome", success=False, error=str(error),
                             processing_time=time.perf_counter() - started)
        result = self.delegate.recognize(processed)
        result.metadata["original_pdf"] = str(input_path.resolve())
        return result
