
"""
---------------------------------------------------------
Module    : base_loader.py
Project   : SmartHTR

Description:
    Abstract base class for all document loaders.
---------------------------------------------------------
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.entities import Document


class BaseLoader(ABC):
    """
    Abstract interface for document loaders.
    """

    @abstractmethod
    def load(
        self,
        file_path: Path,
    ) -> Document:
        """
        Load a document.

        Parameters
        ----------
        file_path : Path
            Path to the input document.

        Returns
        -------
        Document
            Loaded document.
        """
        raise NotImplementedError