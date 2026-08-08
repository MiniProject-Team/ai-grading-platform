"""Central, environment-aware settings for SmartEval."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    input_directory: Path
    log_directory: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        project_root = Path(__file__).resolve().parents[2]
        return cls(
            input_directory=project_root / os.getenv("INPUT_DIRECTORY", "inputs"),
            log_directory=project_root / os.getenv("LOG_DIRECTORY", "logs"),
        )
