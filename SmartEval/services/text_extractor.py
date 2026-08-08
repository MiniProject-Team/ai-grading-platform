"""File-to-text extraction, deliberately separate from document parsing."""

from __future__ import annotations

import json
from pathlib import Path

import fitz


class TextExtractor:
    def extract(self, source: Path) -> str:
        source = source.resolve()
        if not source.exists():
            raise ValueError(f"Input file not found: {source}")
        if source.is_dir():
            files = sorted(source.glob("*.txt"))
            if not files:
                raise ValueError(f"No text files found in: {source}")
            return "\n\n".join(self._read_text(path) for path in files).strip()
        if source.suffix.lower() == ".txt":
            return self._read_text(source).strip()
        if source.suffix.lower() == ".json":
            return self._read_json(source)
        if source.suffix.lower() == ".pdf":
            return self._read_pdf(source)
        raise ValueError(f"Unsupported input format: {source.suffix}")

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> str:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, dict) and isinstance(data.get("text"), str):
            return data["text"].strip()
        raise ValueError(f"JSON requires a string value or 'text' field: {path}")

    @staticmethod
    def _read_pdf(path: Path) -> str:
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf).strip()
