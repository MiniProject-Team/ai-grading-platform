"""Single orchestration point for full-page handwritten OCR."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import cv2

from smarthtr.config.settings import Settings
from smarthtr.core.entities import Document
from smarthtr.cropping.line_cropper import LineCropper
from smarthtr.detection.doctr_detector import DocTRDetector
from smarthtr.document.loader import DocumentLoader
from smarthtr.export.text_exporter import TextExporter
from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor
from smarthtr.preprocessing.padding import LinePreprocessor
from smarthtr.reconstruction.reading_order import ReadingOrderReconstructor
from smarthtr.recognition.trocr_small import TrOCRSmallRecognizer


class OCRPipeline:
    def __init__(
        self,
        settings: Settings,
        loader: DocumentLoader | None = None,
        preprocessor: ImagePreprocessor | None = None,
        detector: DocTRDetector | None = None,
        cropper: LineCropper | None = None,
        line_preprocessor: LinePreprocessor | None = None,
        recognizer: TrOCRSmallRecognizer | None = None,
        reconstructor: ReadingOrderReconstructor | None = None,
        exporter: TextExporter | None = None,
    ) -> None:
        self.settings = settings
        self.loader = loader or DocumentLoader(settings)
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.detector = detector or DocTRDetector()
        self.cropper = cropper or LineCropper()
        self.line_preprocessor = line_preprocessor or LinePreprocessor()
        self.recognizer = recognizer or TrOCRSmallRecognizer(settings)
        self.reconstructor = reconstructor or ReadingOrderReconstructor()
        self.exporter = exporter or TextExporter()
        self.logger = logging.getLogger("smarthtr")

    def run(self, input_path: Path) -> Document:
        started = time.perf_counter()

        self.logger.info("Starting SmartHTR for %s", input_path)

        document = self.loader.load(input_path)

        self.logger.info(
            "Loaded %s page(s)",
            len(document.pages),
        )

        self.process(document)

        output_paths = self.exporter.export(
            document,
            self.settings.output_directory,
        )

        self.logger.info(
            "OCR completed in %.2fs; output: %s",
            time.perf_counter() - started,
            output_paths,
        )

        return document

    def process(self, document: Document) -> Document:
        for page in document.pages:

            # ---------------------------------------------------------
            # 1. FULL-PAGE PREPROCESSING
            # ---------------------------------------------------------
            self.logger.info(
                "Preprocessing page %s",
                page.number,
            )

            self.preprocessor.process(page)

            # ---------------------------------------------------------
            # 2. USE THE PROCESSED IMAGE
            # ---------------------------------------------------------
            processed_image = (
                page.processed_image
                if page.processed_image is not None
                else page.image
            )

            # ---------------------------------------------------------
            # 3. DOCTR DETECTION
            # ---------------------------------------------------------
            self.logger.info(
                "Running DocTR detection on page %s",
                page.number,
            )

            page.detections = self.detector.detect(
                processed_image,
                page.number,
            )

            # ---------------------------------------------------------
            # 4. CROP DETECTED HANDWRITING REGIONS
            # ---------------------------------------------------------
            page.lines = self.cropper.crop(
                processed_image,
                page.detections,
            )

            self.logger.info(
                "Detected %s line(s) on page %s",
                len(page.lines),
                page.number,
            )

            # ---------------------------------------------------------
            # 5. LINE-LEVEL PREPROCESSING
            # ---------------------------------------------------------
            for line in page.lines:
                self.line_preprocessor.process(line)

            # ---------------------------------------------------------
            # 6. HANDWRITING RECOGNITION
            # ---------------------------------------------------------
            self.recognizer.recognize_batch(page.lines)

            # ---------------------------------------------------------
            # 7. RECONSTRUCT READING ORDER
            # ---------------------------------------------------------
            page.lines = self.reconstructor.order(page.lines)

            # ---------------------------------------------------------
            # 8. SAVE DEBUG LINE IMAGES
            # ---------------------------------------------------------
            self._save_debug_lines(page)

        return document

    def _save_debug_lines(self, page) -> None:
        if not self.settings.save_line_images:
            return

        page_directory = (
            self.settings.line_output_directory
            / f"page_{page.number:03d}"
        )

        page_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for line in page.lines:
            image = (
                line.processed_image
                if line.processed_image is not None
                else line.image
            )

            cv2.imwrite(
                str(page_directory / f"line_{line.id:03d}.png"),
                cv2.cvtColor(
                    image,
                    cv2.COLOR_RGB2BGR,
                ),
            )