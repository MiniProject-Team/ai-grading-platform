from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from smarthtr.config.settings import Settings
from smarthtr.core.entities import BoundingBox, Detection, Document, Line, OCRResult, Page
from smarthtr.pipeline.ocr_pipeline import OCRPipeline


class _Loader:
    def __init__(self, document): self.document = document
    def load(self, path): return self.document

class _PagePreprocessor:
    def process(self, page): page.processed_image = page.original_image; return page

class _Detector:
    def detect(self, image, page_number): return [Detection(BoundingBox(.1, .1, .9, .4), .9, page_number)]

class _Cropper:
    def crop(self, image, detections): return [Line(1, 1, detections[0].bbox, image[1:4, 1:9])]

class _LinePreprocessor:
    def process(self, line): line.processed_image = line.image; return line

class _Recognizer:
    def recognize_batch(self, lines):
        for line in lines: line.result = OCRResult(text="complete page text")
        return [line.result for line in lines]


class CompletePipelineTests(unittest.TestCase):
    def test_load_detect_crop_recognize_reconstruct_and_export(self):
        page = Page(1, np.full((10, 10, 3), 255, dtype=np.uint8))
        document = Document(Path("page.jpg"), [page])
        with TemporaryDirectory() as directory:
            pipeline = OCRPipeline(
                settings=Settings(output_directory=Path(directory)),
                loader=_Loader(document), preprocessor=_PagePreprocessor(), detector=_Detector(),
                cropper=_Cropper(), line_preprocessor=_LinePreprocessor(), recognizer=_Recognizer(),
            )
            result = pipeline.run(Path("page.jpg"))
            output = Path(directory) / "page_001.txt"
            self.assertEqual(result.full_text, "complete page text")
            self.assertEqual(output.read_text(encoding="utf-8"), "complete page text\n")
