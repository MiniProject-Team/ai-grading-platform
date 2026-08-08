"""
---------------------------------------------------------
Module    : settings.py
Project   : SmartHTR
Author     : Ayush Bire

Description:
    Centralized application settings.
    Combines project defaults with optional
    environment variables.
---------------------------------------------------------
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from config.defaults import (
    APPLICATION_NAME,
    APPLICATION_VERSION,
    DEFAULT_DPI,
    IMAGE_FORMAT,
    IMAGE_COLOR_MODE,
    LINE_PADDING,
    TARGET_LINE_HEIGHT,
    RECOGNITION_BATCH_SIZE,
    DEFAULT_EXPORT_FORMAT,
    DEFAULT_LOG_LEVEL,
)

load_dotenv()


# ==========================================================
# Application
# ==========================================================

@dataclass(frozen=True)
class AppSettings:
    name: str = APPLICATION_NAME
    version: str = APPLICATION_VERSION


# ==========================================================
# Image
# ==========================================================

@dataclass(frozen=True)
class ImageSettings:
    dpi: int = int(os.getenv("DEFAULT_DPI", DEFAULT_DPI))
    format: str = os.getenv("IMAGE_FORMAT", IMAGE_FORMAT)
    color_mode: str = os.getenv("IMAGE_COLOR_MODE", IMAGE_COLOR_MODE)


# ==========================================================
# Preprocessing
# ==========================================================

@dataclass(frozen=True)
class PreprocessingSettings:
    line_padding: int = int(
        os.getenv("LINE_PADDING", LINE_PADDING)
    )

    target_line_height: int = int(
        os.getenv(
            "TARGET_LINE_HEIGHT",
            TARGET_LINE_HEIGHT,
        )
    )


# ==========================================================
# Recognition
# ==========================================================

@dataclass(frozen=True)
class RecognitionSettings:
    batch_size: int = int(
        os.getenv(
            "RECOGNITION_BATCH_SIZE",
            RECOGNITION_BATCH_SIZE,
        )
    )

    model_name: str = os.getenv(
        "RECOGNITION_MODEL",
        "microsoft/trocr-small-handwritten",
    )


# ==========================================================
# Export
# ==========================================================

@dataclass(frozen=True)
class ExportSettings:
    default_format: str = os.getenv(
        "DEFAULT_EXPORT_FORMAT",
        DEFAULT_EXPORT_FORMAT,
    )


# ==========================================================
# Logging
# ==========================================================

@dataclass(frozen=True)
class LoggingSettings:
    level: str = os.getenv(
        "LOG_LEVEL",
        DEFAULT_LOG_LEVEL,
    )


# ==========================================================
# Root Settings
# ==========================================================

@dataclass(frozen=True)
class Settings:
    app: AppSettings = AppSettings()
    image: ImageSettings = ImageSettings()
    preprocessing: PreprocessingSettings = PreprocessingSettings()
    recognition: RecognitionSettings = RecognitionSettings()
    export: ExportSettings = ExportSettings()
    logging: LoggingSettings = LoggingSettings()


settings = Settings()