from __future__ import annotations

from pathlib import Path

from cropping import LineCropper
from detection import DocTRDetector
from document_loader import DocumentLoader
from ordering import ReadingOrder
from postprocessing import SpellCorrector, TextCleaner
from preprocessing.line import LinePreprocessor
from preprocessing.page import PagePreprocessor
from recognition.trocr_recognizer import TrOCRRecognizer

from core.entities import Document


class OCRPipeline:
    """Run the SmartHTR OCR workflow for a document."""

    def __init__(
        self,
        loader=None,
        page_preprocessor=None,
        detector=None,
        ordering=None,
        cropper=None,
        line_preprocessor=None,
        recognizer=None,
        postprocessors: list | None = None,
    ) -> None:
        self.loader = loader or DocumentLoader()
        self.page_preprocessor = page_preprocessor or PagePreprocessor()
        self.detector = detector or DocTRDetector()
        self.ordering = ordering or ReadingOrder()
        self.cropper = cropper or LineCropper()
        self.line_preprocessor = line_preprocessor or LinePreprocessor()
        self.recognizer = recognizer or TrOCRRecognizer()
        self.postprocessors = postprocessors or [TextCleaner(), SpellCorrector()]

    def run(self, source_path: str | Path) -> Document:
        document = self.loader.load(source_path)
        return self.process(document)

    def process(self, document: Document) -> Document:
        for page in document.pages:
            self.page_preprocessor.process(page)
            self.detector.detect(page)
            self.ordering.order(page)
            self.cropper.crop(page)

            for line in page.lines:
                self.line_preprocessor.process(line)
                self.recognizer.recognize(line)
                for postprocessor in self.postprocessors:
                    postprocessor.process(line)

        return document

