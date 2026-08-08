"""Lazy model loading and portable CPU/CUDA selection."""

from __future__ import annotations

import logging

import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from smarthtr.config.settings import Settings
from smarthtr.core.exceptions import RecognitionError


class ModelManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.device = self._resolve_device()
        self.processor = None
        self.model = None
        self.logger = logging.getLogger("smarthtr")

    def _resolve_device(self) -> torch.device:
        if self.settings.device not in {"auto", "cpu", "cuda"}:
            raise RecognitionError("DEVICE must be auto, cpu, or cuda")
        if self.settings.device == "cuda" and not torch.cuda.is_available():
            raise RecognitionError("DEVICE=cuda was requested but CUDA is unavailable")
        return torch.device("cuda" if self.settings.device == "cuda" or (self.settings.device == "auto" and torch.cuda.is_available()) else "cpu")

    def load_trocr(self) -> tuple[TrOCRProcessor, VisionEncoderDecoderModel]:
        if self.processor is not None and self.model is not None:
            return self.processor, self.model
        try:
            self.logger.info("Loading TrOCR model '%s' on %s", self.settings.model_name, self.device)
            self.settings.model_cache_directory.mkdir(parents=True, exist_ok=True)
            self.processor = TrOCRProcessor.from_pretrained(self.settings.model_name, cache_dir=str(self.settings.model_cache_directory), use_fast=False)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.settings.model_name, cache_dir=str(self.settings.model_cache_directory)).to(self.device)
            self.model.eval()
            return self.processor, self.model
        except Exception as error:
            raise RecognitionError(f"Unable to load recognizer model: {error}") from error
