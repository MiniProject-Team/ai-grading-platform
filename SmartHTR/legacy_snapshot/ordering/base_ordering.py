"""
---------------------------------------------------------
Module    : base_ordering.py
Project   : SmartHTR

Description:
    Abstract interface for reading-order algorithms.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.entities import Page


class BaseOrdering(ABC):
    """
    Base interface for reading-order generation.
    """

    @abstractmethod
    def order(
        self,
        page: Page,
    ) -> None:
        """
        Reorder page detections.
        """
        raise NotImplementedError