from __future__ import annotations

from pathlib import Path

import cv2
import fitz

from smarthtr.core.entities import Document


class PreprocessedPdfExporter:
    """
    Creates an OCR-ready PDF from SmartHTR processed page images.

    The PDF uses:
    - A4 page dimensions
    - JPEG-compressed page images
    - Configurable JPEG quality
    """

    A4_WIDTH = 595
    A4_HEIGHT = 842

    def __init__(self, jpeg_quality: int = 85) -> None:
        if not 1 <= jpeg_quality <= 100:
            raise ValueError("jpeg_quality must be between 1 and 100")

        self.jpeg_quality = jpeg_quality

    def export(
        self,
        document: Document,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf = fitz.open()

        try:
            for page in document.pages:
                if page.processed_image is None:
                    raise ValueError(
                        f"Page {page.number} has no processed image"
                    )

                image = page.processed_image

                image_bgr = cv2.cvtColor(
                    image,
                    cv2.COLOR_RGB2BGR,
                )

                success, encoded = cv2.imencode(
                    ".jpg",
                    image_bgr,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        self.jpeg_quality,
                        cv2.IMWRITE_JPEG_OPTIMIZE,
                        1,
                    ],
                )

                if not success:
                    raise RuntimeError(
                        f"Failed to encode page {page.number}"
                    )

                pdf_page = pdf.new_page(
                    width=self.A4_WIDTH,
                    height=self.A4_HEIGHT,
                )

                pdf_page.insert_image(
                    fitz.Rect(
                        0,
                        0,
                        self.A4_WIDTH,
                        self.A4_HEIGHT,
                    ),
                    stream=encoded.tobytes(),
                    keep_proportion=True,
                )

            pdf.save(
                output_path,
                garbage=4,
                clean=True,
                deflate=True,
            )

        finally:
            pdf.close()

        return output_path