import unittest

import numpy as np

from smarthtr.core.entities import Page
from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor


class PreprocessingTests(unittest.TestCase):
    def test_produces_rgb_page_image(self):
        image = np.full((80, 120, 3), 255, dtype=np.uint8)
        image[30:50, 20:100] = 0
        page = ImagePreprocessor().process(Page(number=1, original_image=image))
        self.assertEqual(page.image.shape, image.shape)
        self.assertEqual(page.image.ndim, 3)
