"""Current baseline recognizer; replaceable through the Recognizer interface."""

from __future__ import annotations

import torch
from PIL import Image

from smarthtr.config.settings import Settings
from smarthtr.core.entities import Line, OCRResult
from smarthtr.core.interfaces import Recognizer
from smarthtr.models.model_manager import ModelManager


class TrOCRSmallRecognizer(Recognizer):
    def __init__(self, settings: Settings, model_manager: ModelManager | None = None) -> None:
        self.settings = settings
        self.model_manager = model_manager or ModelManager(settings)
        self.processor = None
        self.model = None

    def load_model(self) -> None:
        self.processor, self.model = self.model_manager.load_trocr()

    def recognize(self, line: Line) -> OCRResult:
        return self.recognize_batch([line])[0]

    def recognize_batch(self, lines: list[Line]) -> list[OCRResult]:
        if not lines:
            return []
        self.load_model()
        images = [Image.fromarray(line.processed_image if line.processed_image is not None else line.image) for line in lines]
        pixels = self.processor(images=images, return_tensors="pt").pixel_values.to(self.model_manager.device)
        with torch.inference_mode():
            generated = self.model.generate(pixels, max_new_tokens=self.settings.max_new_tokens, num_beams=self.settings.num_beams)
        texts = self.processor.batch_decode(generated, skip_special_tokens=True)
        results = [OCRResult(text=text.strip(), model_name=self.settings.model_name) for text in texts]
        for line, result in zip(lines, results):
            line.result = result
        return results
