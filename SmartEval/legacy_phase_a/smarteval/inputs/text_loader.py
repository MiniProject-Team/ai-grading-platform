"""Load UTF-8 text files and ordered SmartHTR page-text directories."""

from __future__ import annotations

from pathlib import Path

from smarteval.core.exceptions import InputValidationError

from .base_loader import BaseInputLoader


class TextInputLoader(BaseInputLoader):
    def load(self, source: Path) -> str:
        if source.is_file():
            return self._read_file(source)
        if source.is_dir():
            files = sorted(source.glob("*.txt"))
            if not files:
                raise InputValidationError(f"No .txt files found in: {source}")
            return "\n\n".join(self._read_file(path) for path in files)
        raise InputValidationError(f"Input source not found: {source}")

    @staticmethod
    def _read_file(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError as error:
            raise InputValidationError(f"Input must be UTF-8 text: {path}") from error
