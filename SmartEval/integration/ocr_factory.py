from __future__ import annotations

from config.settings import Settings

from .ocr_service import ILovePDFOCRService, OCRService
from .smarthtr_client import TrOCROCRService
from .smarthtr_preprocessor import PreprocessedILovePDFOCRService, SmartHTRPreprocessor
from .smarthtr_preprocessor import PreprocessedChromeOCRService
from .chrome_ocr_service import ChromeOCRService


def create_ocr_service(settings: Settings) -> OCRService:
    if settings.ocr_provider == "chrome":
        return PreprocessedChromeOCRService(
            ChromeOCRService(settings), SmartHTRPreprocessor(enforce_upload_limit=False),
            settings.output_directory,
        )
    if settings.ocr_provider == "trocr":
        return TrOCROCRService()
    if settings.ocr_provider == "ilovepdf":
        service = ILovePDFOCRService(
            public_key=settings.ilovepdf_public_key,
            secret_key=settings.ilovepdf_secret_key,
            region=settings.ilovepdf_region,
            timeout=settings.ilovepdf_timeout,
        )
        return PreprocessedILovePDFOCRService(service, SmartHTRPreprocessor())
    raise ValueError("OCR_PROVIDER must be 'trocr', 'ilovepdf', or 'chrome'.")
