"""
---------------------------------------------------------
Module    : model_manager.py
Project   : SmartHTR

Description:
    Singleton manager for OCR models.
---------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path

from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
)

from config.paths import PRETRAINED_MODELS_DIR
from config.settings import settings


class ModelManager:
    """
    Loads and caches OCR models.
    """

    _processor = None
    _model = None

    @classmethod
    def get_processor(cls):

        if cls._processor is None:

            cls._processor = TrOCRProcessor.from_pretrained(
    settings.recognition.model_name,
    cache_dir=str(PRETRAINED_MODELS_DIR),
    use_fast=False,
)

        return cls._processor

    @classmethod
    def get_model(cls):

        if cls._model is None:

            cls._model = VisionEncoderDecoderModel.from_pretrained(
                settings.recognition.model_name,
                cache_dir=str(PRETRAINED_MODELS_DIR),
            )

            cls._model.eval()

        return cls._model