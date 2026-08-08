"""
---------------------------------------------------------
Module    : metadata.py
Project   : SmartHTR

Description:
    Metadata container shared across the OCR pipeline.
---------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metadata:
    """
    Generic metadata container.

    Stores processing information produced by
    different pipeline stages.
    """

    values: dict[str, Any] = field(default_factory=dict)

    def add(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update a metadata value.
        """
        self.values[key] = value

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a metadata value.
        """
        return self.values.get(key, default)

    def update(
        self,
        values: dict[str, Any],
    ) -> None:
        """
        Merge multiple metadata values.
        """
        self.values.update(values)

    def clear(self) -> None:
        """
        Remove all metadata.
        """
        self.values.clear()