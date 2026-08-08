"""PDF rasterization using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz
import numpy as np

from smarthtr.core.exceptions import DocumentLoadError
from smarthtr.utils.image_utils import ensure_rgb


def pdf_to_images(path: Path, dpi: int) -> list[np.ndarray]:
    try:
        with fitz.open(path) as pdf:
            scale = dpi / 72
            matrix = fitz.Matrix(scale, scale)
            images = []
            for pdf_page in pdf:
                pixmap = pdf_page.get_pixmap(matrix=matrix, alpha=False)
                image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                    pixmap.height, pixmap.width, pixmap.n
                )
                images.append(ensure_rgb(image))
            return images
    except Exception as error:
        raise DocumentLoadError(f"Unable to read PDF '{path}': {error}") from error
