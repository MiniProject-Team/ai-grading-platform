"""
Recognition result entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .metadata import Metadata


@dataclass(slots=True)
class Recognition:
    """
    Recognition output for one text line.
    """

    text: str = ""

    confidence: float | None = None

    model_name: str = ""

    processing_time: float | None = None

    metadata: Metadata = field(
        default_factory=Metadata
    )