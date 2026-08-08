"""
---------------------------------------------------------
Module    : base_detector.py
Project   : SmartHTR

Description:
    Abstract interface for text detectors.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.entities import Page


class BaseDetector(ABC):
    """
    Base interface for text detection.
    """

    @abstractmethod
    def detect(
        self,
        page: Page,
    ) -> None:
        """
        Detect text regions.
        """
        raise NotImplementedError