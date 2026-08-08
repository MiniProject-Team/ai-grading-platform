"""
---------------------------------------------------------
Module    : trocr_recognizer.py
Project   : SmartHTR

Description:
    Handwritten OCR using TrOCR Small.
---------------------------------------------------------
"""

from __future__ import annotations

import time

import torch
from PIL import Image

from core.entities import Line

from .base_recognizer import BaseRecognizer
from .model_manager import ModelManager


class TrOCRRecognizer(BaseRecognizer):
    """
    Recognize handwritten text using TrOCR.
    """

    def __init__(self):

        self.processor = ModelManager.get_processor()

        self.model = ModelManager.get_model()

    def recognize(
        self,
        line: Line,
    ) -> None:

        image = line.processed_image

        if image is None:

            image = line.image

        if len(image.shape) == 2:

            pil = Image.fromarray(image)

        else:

            pil = Image.fromarray(image)

        start = time.perf_counter()

        pixel_values = self.processor(
            images=pil,
            return_tensors="pt",
        ).pixel_values

        with torch.no_grad():

            generated = self.model.generate(
                pixel_values
            )

        text = self.processor.batch_decode(
            generated,
            skip_special_tokens=True,
        )[0]

        elapsed = time.perf_counter() - start

        line.recognition.text = text

        line.recognition.processing_time = elapsed

        line.recognition.model_name = (
            "microsoft/trocr-small-handwritten"
        )