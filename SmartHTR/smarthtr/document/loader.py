"""Load one image or every page from a PDF into domain objects."""

from __future__ import annotations

from pathlib import Path

import cv2

from smarthtr.config.settings import Settings
from smarthtr.core.entities import Document, Page
from smarthtr.core.exceptions import DocumentLoadError

from .pdf_converter import pdf_to_images


class DocumentLoader:
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def load(self, path: Path) -> Document:
        path = path.resolve()
        if not path.is_file():
            raise DocumentLoadError(f"Input file not found: {path}")
        if path.suffix.lower() == ".pdf":
            images = pdf_to_images(path, self.settings.image_dpi)
        elif path.suffix.lower() in self.image_extensions:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise DocumentLoadError(f"Unable to read image: {path}")
            images = [cv2.cvtColor(image, cv2.COLOR_BGR2RGB)]
        else:
            raise DocumentLoadError(f"Unsupported input type: {path.suffix}")
        if not images:
            raise DocumentLoadError(f"No pages found in: {path}")
        return Document(path=path, pages=[Page(number=index, original_image=image) for index, image in enumerate(images, 1)])
