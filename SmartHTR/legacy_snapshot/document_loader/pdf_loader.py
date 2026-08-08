"""
---------------------------------------------------------
Module    : pdf_loader.py
Project   : SmartHTR

Description:
    Loads PDF documents into Document entities.
---------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path

import fitz
import numpy as np

from core.entities import Document, Page
from core.exceptions import DocumentLoadError

from .base_loader import BaseLoader


class PDFLoader(BaseLoader):
    """
    PDF document loader.
    """

    def __init__(
        self,
        dpi: int = 300,
    ) -> None:

        self.dpi = dpi

    def load(
        self,
        file_path: Path,
    ) -> Document:

        if not file_path.exists():
            raise DocumentLoadError(
                f"File not found: {file_path}"
            )

        try:

            pdf = fitz.open(file_path)

            document = Document(
                id=file_path.stem,
                file_name=file_path.name,
                file_path=file_path,
            )

            zoom = self.dpi / 72

            matrix = fitz.Matrix(zoom, zoom)

            for index, page in enumerate(pdf):

                pixmap = page.get_pixmap(
                    matrix=matrix,
                    alpha=False,
                )

                image = np.frombuffer(
                    pixmap.samples,
                    dtype=np.uint8,
                ).reshape(
                    pixmap.height,
                    pixmap.width,
                    pixmap.n,
                )

                document.pages.append(

                    Page(
                        page_number=index + 1,
                        original_image=image,
                    )

                )

            pdf.close()

            return document

        except Exception as error:

            raise DocumentLoadError(
                f"Unable to load PDF: {error}"
            ) from error