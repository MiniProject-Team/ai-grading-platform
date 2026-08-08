"""
---------------------------------------------------------
Module    : interfaces.py
Project   : SmartHTR

Description:
    Reserved for project-wide shared interfaces.

    Module-specific abstract base classes should remain
    inside their respective packages:

    - document_loader/base_loader.py
    - detection/base_detector.py
    - cropping/base_cropper.py
    - recognition/base_recognizer.py
    - exporters/base_exporter.py

    This file should only contain interfaces that are
    shared across multiple independent modules.
---------------------------------------------------------
"""

from __future__ import annotations

from typing import Protocol


class PipelineComponent(Protocol):
    """
    Optional shared protocol for future pipeline
    components.

    Currently kept as a placeholder to preserve the
    frozen architecture.
    """

    def __repr__(self) -> str:
        ...