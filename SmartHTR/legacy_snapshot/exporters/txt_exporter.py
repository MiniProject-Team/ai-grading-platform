"""Plain-text export for a processed document."""

from __future__ import annotations

from pathlib import Path

from core.entities import Document

from .base_exporter import BaseExporter


class TextExporter(BaseExporter):
    """Export recognized document text to a UTF-8 file."""

    def export(self, document: Document, output_path: Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for page in document.pages:
                file.write(f"========== Page {page.page_number} ==========\n\n")
                for line in page.lines:
                    file.write(f"{line.recognition.text}\n")
                file.write("\n")
