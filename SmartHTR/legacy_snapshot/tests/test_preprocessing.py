import unittest

import numpy as np

from core.entities import Page
from preprocessing.page import PagePreprocessor


class PagePreprocessorTests(unittest.TestCase):
    def test_preserves_a_valid_rgb_image(self) -> None:
        image = np.full((64, 96, 3), 255, dtype=np.uint8)
        image[20:40, 30:70] = 0
        page = Page(page_number=1, original_image=image)

        PagePreprocessor().process(page)

        self.assertIsNotNone(page.processed_image)
        self.assertEqual(page.processed_image.ndim, 3)
        self.assertEqual(page.processed_image.shape[2], 3)
