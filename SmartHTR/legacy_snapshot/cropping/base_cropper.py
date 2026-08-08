"""
---------------------------------------------------------
Module    : base_cropper.py
Project   : SmartHTR

Description:
    Abstract interface for line croppers.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.entities import Page


class BaseCropper(ABC):
    """
    Base interface for line croppers.
    """

    @abstractmethod
    def crop(
        self,
        page: Page,
    ) -> None:
        """
        Crop text regions from a page.
        """
        raise NotImplementedError