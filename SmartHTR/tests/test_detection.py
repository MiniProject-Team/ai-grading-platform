import unittest

import numpy as np

from smarthtr.detection.doctr_detector import DocTRDetector


class DetectionTests(unittest.TestCase):
    def test_parses_doctr_word_prediction(self):
        detections = DocTRDetector.parse_predictions(np.array([[0.1, 0.2, 0.8, 0.4, 0.95]]), 1)
        self.assertEqual(len(detections), 1)
        self.assertAlmostEqual(detections[0].bbox.left, 0.1)
        self.assertAlmostEqual(detections[0].confidence, 0.95)

    def test_groups_words_on_the_same_row_into_a_line(self):
        predictions = np.array([
            [0.1, 0.10, 0.2, 0.14, 0.9],
            [0.3, 0.11, 0.4, 0.15, 0.8],
            [0.1, 0.30, 0.2, 0.34, 0.9],
        ])
        detections = DocTRDetector.parse_predictions(predictions, 1)
        self.assertEqual(len(detections), 2)
        self.assertAlmostEqual(detections[0].bbox.right, 0.4)
