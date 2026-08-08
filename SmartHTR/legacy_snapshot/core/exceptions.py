"""
---------------------------------------------------------
Module    : exceptions.py
Project   : SmartHTR

Description:
    Custom exception hierarchy for SmartHTR.
---------------------------------------------------------
"""

from __future__ import annotations


class SmartHTRError(Exception):
    """
    Base exception for the SmartHTR project.
    """

    pass


# ==========================================================
# Configuration
# ==========================================================

class ConfigurationError(SmartHTRError):
    """
    Raised when configuration is invalid.
    """

    pass


# ==========================================================
# Document Loader
# ==========================================================

class DocumentLoadError(SmartHTRError):
    """
    Raised when a document cannot be loaded.
    """

    pass


# ==========================================================
# Preprocessing
# ==========================================================

class PreprocessingError(SmartHTRError):
    """
    Raised when preprocessing fails.
    """

    pass


# ==========================================================
# Detection
# ==========================================================

class DetectionError(SmartHTRError):
    """
    Raised when text detection fails.
    """

    pass


# ==========================================================
# Reading Order
# ==========================================================

class OrderingError(SmartHTRError):
    """
    Raised when reading order generation fails.
    """

    pass


# ==========================================================
# Cropping
# ==========================================================

class CroppingError(SmartHTRError):
    """
    Raised when cropping fails.
    """

    pass


# ==========================================================
# Recognition
# ==========================================================

class RecognitionError(SmartHTRError):
    """
    Raised when OCR recognition fails.
    """

    pass


# ==========================================================
# Post Processing
# ==========================================================

class PostProcessingError(SmartHTRError):
    """
    Raised when text post-processing fails.
    """

    pass


# ==========================================================
# Export
# ==========================================================

class ExportError(SmartHTRError):
    """
    Raised when exporting fails.
    """

    pass


# ==========================================================
# Pipeline
# ==========================================================

class PipelineError(SmartHTRError):
    """
    Raised when the OCR pipeline fails.
    """

    pass