"""JSON export for a processed document."""

from __future__ import annotations

import json
from pathlib import Path

from core.entities import Document

from .base_exporter import BaseExporter


class JsonExporter(BaseExporter):
    """Export recognized document text and confidence as JSON."""

    def export(self, document: Document, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "file_name": document.file_name,
            "pages": [
                {
                    "page_number": page.page_number,
                    "lines": [
                        {
                            "id": line.id,
                            "text": line.recognition.text,
                            "confidence": line.recognition.confidence,
                        }
                        for line in page.lines
                    ],
                }
                for page in document.pages
            ],
        }
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
