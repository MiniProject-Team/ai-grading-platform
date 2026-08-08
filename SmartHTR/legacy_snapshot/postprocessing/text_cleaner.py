"""Line-level OCR text cleanup."""

from __future__ import annotations

import re

from core.entities import Line


class TextCleaner:
    """Normalize whitespace in one recognized line."""

    def process(self, line: Line) -> None:
        line.recognition.text = re.sub(
            r"\s+",
            " ",
            line.recognition.text,
        ).strip()
