from pathlib import Path
import unittest

import numpy as np

from core.entities import BoundingBox, Detection, Document, Line, Page
from pipeline import OCRPipeline


class _Loader:
    def __init__(self, document: Document) -> None:
        self.document = document

    def load(self, source_path: str | Path) -> Document:
        return self.document


class _PagePreprocessor:
    def process(self, page: Page) -> None:
        page.processed_image = page.original_image


class _Detector:
    def detect(self, page: Page) -> None:
        page.detections = [
            Detection(
                id=1,
                page_number=page.page_number,
                bbox=BoundingBox(0.1, 0.1, 0.9, 0.4),
                confidence=0.99,
            )
        ]


class _Ordering:
    def order(self, page: Page) -> None:
        page.detections.sort(key=lambda detection: detection.bbox.top)


class _Cropper:
    def crop(self, page: Page) -> None:
        detection = page.detections[0]
        page.lines = [
            Line(
                id=1,
                page_number=page.page_number,
                bbox=detection.bbox,
                image=page.image[1:4, 1:9],
            )
        ]


class _LinePreprocessor:
    def process(self, line: Line) -> None:
        line.processed_image = line.image


class _Recognizer:
    def recognize(self, line: Line) -> None:
        line.recognition.text = "  handwritten   text  "


class PipelineTests(unittest.TestCase):
    def test_processes_document_through_every_stage(self) -> None:
        page = Page(
            page_number=1,
            original_image=np.full((10, 10, 3), 255, dtype=np.uint8),
        )
        document = Document(
            id="test-document",
            file_name="test.png",
            file_path=Path("test.png"),
            pages=[page],
        )
        pipeline = OCRPipeline(
            loader=_Loader(document),
            page_preprocessor=_PagePreprocessor(),
            detector=_Detector(),
            ordering=_Ordering(),
            cropper=_Cropper(),
            line_preprocessor=_LinePreprocessor(),
            recognizer=_Recognizer(),
        )

        result = pipeline.run("test.png")

        self.assertIs(result, document)
        self.assertEqual(len(result.pages[0].detections), 1)
        self.assertEqual(len(result.pages[0].lines), 1)
        self.assertEqual(
            result.pages[0].lines[0].recognition.text,
            "handwritten text",
        )
