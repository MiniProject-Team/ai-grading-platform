from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseInputLoader(ABC):
    @abstractmethod
    def load(self, source: Path) -> str: ...
