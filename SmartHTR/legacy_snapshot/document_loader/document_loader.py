"""
---------------------------------------------------------
Module    : document_loader.py
Project   : SmartHTR

Description:
    Selects the appropriate loader based on file type.
---------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path

from core.entities import Document
from core.exceptions import DocumentLoadError

from .image_loader import ImageLoader
from .pdf_loader import PDFLoader


class DocumentLoader:
    """
    Factory class for loading supported documents.
    """

    IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tif",
        ".tiff",
    }

    PDF_EXTENSION = ".pdf"

    def __init__(
        self,
        dpi: int = 300,
    ) -> None:

        self.pdf_loader = PDFLoader(dpi=dpi)

        self.image_loader = ImageLoader()

    def load(
        self,
        file_path: Path,
    ) -> Document:

        suffix = file_path.suffix.lower()

        if suffix == self.PDF_EXTENSION:
            return self.pdf_loader.load(file_path)

        if suffix in self.IMAGE_EXTENSIONS:
            return self.image_loader.load(file_path)

        raise DocumentLoadError(
            f"Unsupported file format: {suffix}"
        )