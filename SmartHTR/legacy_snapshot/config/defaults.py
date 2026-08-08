"""
---------------------------------------------------------
Module    : defaults.py
Project   : SmartHTR
Author    : Ayush Bire

Description:
    Contains project-wide default configuration values.
    These values are used unless overridden by settings
    or environment variables.
---------------------------------------------------------
"""

from __future__ import annotations


# ==========================================================
# Application
# ==========================================================

APPLICATION_NAME = "SmartHTR"

APPLICATION_VERSION = "1.0.0"


# ==========================================================
# Image Processing
# ==========================================================

DEFAULT_DPI = 300

IMAGE_FORMAT = "png"

IMAGE_COLOR_MODE = "RGB"


# ==========================================================
# Page Preprocessing
# ==========================================================

SAVE_DEBUG_IMAGES = True

REMOVE_SHADOWS = True

REMOVE_BORDERS = True

DESKEW_ENABLED = True

DENOISE_ENABLED = True

CONTRAST_ENHANCEMENT = True


# ==========================================================
# Line Preprocessing
# ==========================================================

LINE_PADDING = 10

TARGET_LINE_HEIGHT = 64


# ==========================================================
# Detection
# ==========================================================

DETECTION_CONFIDENCE_THRESHOLD = 0.30


# ==========================================================
# Recognition
# ==========================================================

RECOGNITION_BATCH_SIZE = 8


# ==========================================================
# Export
# ==========================================================

DEFAULT_EXPORT_FORMAT = "txt"


# ==========================================================
# Logging
# ==========================================================

DEFAULT_LOG_LEVEL = "INFO"