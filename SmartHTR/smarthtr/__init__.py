"""SmartHTR: full-page handwritten text recognition."""

from .core.entities import Document, OCRResult, Page
from .pipeline.ocr_pipeline import OCRPipeline

__all__ = ["Document", "OCRPipeline", "OCRResult", "Page"]
