"""Export complete reconstructed text for each document page."""

from __future__ import annotations

from pathlib import Path

from smarthtr.core.entities import Document
from smarthtr.core.exceptions import ExportError


class TextExporter:
    def export(self, document: Document, output_directory: Path) -> list[Path]:
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
            paths = []
            for page in document.pages:
                path = output_directory / f"page_{page.number:03d}.txt"
                path.write_text(page.text + ("\n" if page.text else ""), encoding="utf-8")
                paths.append(path)
            return paths
        except OSError as error:
            raise ExportError(f"Unable to export OCR text: {error}") from error
