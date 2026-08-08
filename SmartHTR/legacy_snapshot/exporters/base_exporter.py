"""
---------------------------------------------------------
Module    : base_exporter.py
Project   : SmartHTR

Description:
    Abstract interface for exporters.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.entities import Document


class BaseExporter(ABC):
    """
    Base exporter interface.
    """

    @abstractmethod
    def export(
        self,
        document: Document,
        output_path: Path,
    ) -> None:
        """
        Export OCR results.
        """
        raise NotImplementedError