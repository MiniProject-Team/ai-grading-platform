"""
SmartHTR Core Package.
"""

from .exceptions import (
    SmartHTRError,
    ConfigurationError,
    DocumentLoadError,
    PreprocessingError,
    DetectionError,
    OrderingError,
    CroppingError,
    RecognitionError,
    PostProcessingError,
    ExportError,
    PipelineError,
)

from .entities import (
    BoundingBox,
    Detection,
    Document,
    Line,
    Metadata,
    Page,
    Recognition,
)

__all__ = [
    "BoundingBox",
    "Detection",
    "Document",
    "Line",
    "Metadata",
    "Page",
    "Recognition",
    "SmartHTRError",
    "ConfigurationError",
    "DocumentLoadError",
    "PreprocessingError",
    "DetectionError",
    "OrderingError",
    "CroppingError",
    "RecognitionError",
    "PostProcessingError",
    "ExportError",
    "PipelineError",
]