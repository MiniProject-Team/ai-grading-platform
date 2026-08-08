"""Load plain-text JSON input documents without assuming later schemas."""

from __future__ import annotations

import json
from pathlib import Path

from smarteval.core.exceptions import InputValidationError

from .base_loader import BaseInputLoader


class JsonInputLoader(BaseInputLoader):
    def load(self, source: Path) -> str:
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InputValidationError(f"Invalid JSON input: {source}") from error
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, dict) and isinstance(data.get("text"), str):
            return data["text"].strip()
        raise InputValidationError(f"JSON input needs a string value or a 'text' field: {source}")
