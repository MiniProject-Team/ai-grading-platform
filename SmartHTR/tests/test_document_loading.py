from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import fitz
import numpy as np

from smarthtr.config.settings import Settings
from smarthtr.document.loader import DocumentLoader


class DocumentLoadingTests(unittest.TestCase):
    def test_loads_image(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "page.jpg"
            cv2.imwrite(str(path), np.full((20, 30, 3), 255, dtype=np.uint8))
            document = DocumentLoader(Settings()).load(path)
        self.assertEqual(len(document.pages), 1)
        self.assertEqual(document.pages[0].image.shape, (20, 30, 3))

    def test_loads_pdf(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "page.pdf"
            pdf = fitz.open()
            pdf.new_page()
            pdf.save(path)
            pdf.close()
            document = DocumentLoader(Settings(image_dpi=72)).load(path)
        self.assertEqual(len(document.pages), 1)
