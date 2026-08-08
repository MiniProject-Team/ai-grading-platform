import unittest

import numpy as np

from core.entities import Page
from detection.doctr_detector import DocTRDetector


class DocTRDetectorTests(unittest.TestCase):
    def test_parses_current_doctr_word_predictions(self) -> None:
        page = Page(
            page_number=1,
            original_image=np.zeros((16, 16, 3), dtype=np.uint8),
        )
        detector = object.__new__(DocTRDetector)
        prediction = [{"words": np.array([[0.1, 0.2, 0.8, 0.4, 0.95]])}]

        detector._parse_predictions(page, prediction)

        self.assertEqual(len(page.detections), 1)
        self.assertAlmostEqual(page.detections[0].bbox.left, 0.1)
        self.assertAlmostEqual(page.detections[0].confidence, 0.95)
