"""
---------------------------------------------------------
Module    : document.py
Project   : SmartHTR

Description:
    Represents one document processed by SmartHTR.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .metadata import Metadata
from .page import Page


@dataclass(slots=True)
class Document:
    """
    Root document entity.
    """

    id: str

    file_name: str

    file_path: Path

    pages: list[Page] = field(default_factory=list)

    metadata: Metadata = field(default_factory=Metadata)

    @property
    def total_pages(self) -> int:
        """
        Returns
        -------
        int
            Number of pages in the document.
        """
        return len(self.pages)