"""
---------------------------------------------------------
Module    : image_loader.py
Project   : SmartHTR

Description:
    Loads image files into a Document entity.
---------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import cv2

from core.entities import Document, Page
from core.exceptions import DocumentLoadError

from .base_loader import BaseLoader


class ImageLoader(BaseLoader):
    """
    Loads image documents.
    """

    def load(
        self,
        file_path: Path,
    ) -> Document:

        if not file_path.exists():
            raise DocumentLoadError(
                f"File not found: {file_path}"
            )

        image = cv2.imread(str(file_path))

        if image is None:
            raise DocumentLoadError(
                f"Unable to read image: {file_path}"
            )

        # OpenCV loads BGR -> convert to RGB
        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        document = Document(
            id=str(uuid4()),
            file_name=file_path.name,
            file_path=file_path,
        )

        document.pages.append(
            Page(
                page_number=1,
                original_image=image,
            )
        )

        return document