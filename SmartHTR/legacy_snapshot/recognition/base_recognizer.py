"""
---------------------------------------------------------
Module    : base_recognizer.py
Project   : SmartHTR

Description:
    Abstract interface for OCR recognizers.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.entities import Line


class BaseRecognizer(ABC):
    """
    Base interface for OCR recognizers.
    """

    @abstractmethod
    def recognize(
        self,
        line: Line,
    ) -> None:
        """
        Recognize text from a line image.
        """
        raise NotImplementedError