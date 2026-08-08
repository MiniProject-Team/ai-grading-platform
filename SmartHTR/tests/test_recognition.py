import unittest

import numpy as np

from smarthtr.core.entities import BoundingBox, Line, OCRResult
from smarthtr.core.interfaces import Recognizer


class _FakeRecognizer(Recognizer):
    def load_model(self): pass
    def recognize(self, line): return self.recognize_batch([line])[0]
    def recognize_batch(self, lines):
        return [OCRResult(text="recognized") for _ in lines]


class RecognitionTests(unittest.TestCase):
    def test_recognizer_contract_supports_batches(self):
        line = Line(1, 1, BoundingBox(0, 0, 1, 1), np.zeros((4, 4, 3), dtype=np.uint8))
        self.assertEqual(_FakeRecognizer().recognize(line).text, "recognized")
