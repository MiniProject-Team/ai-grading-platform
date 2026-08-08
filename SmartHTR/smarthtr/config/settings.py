"""Central configuration for local and Colab execution."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    model_name: str = "microsoft/trocr-small-handwritten"
    device: str = "auto"
    max_new_tokens: int = 128
    num_beams: int = 5
    image_dpi: int = 300
    input_directory: Path = Path("test_images")
    output_directory: Path = Path("outputs/text")
    line_output_directory: Path = Path("outputs/lines")
    debug_directory: Path = Path("outputs/debug")
    model_cache_directory: Path = Path("pretrained_models")
    log_directory: Path = Path("logs")
    save_line_images: bool = False

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        defaults = cls()
        project_root = Path(__file__).resolve().parents[2]
        return cls(
            model_name=os.getenv("MODEL_NAME", defaults.model_name),
            device=os.getenv("DEVICE", defaults.device).lower(),
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", defaults.max_new_tokens)),
            num_beams=int(os.getenv("NUM_BEAMS", defaults.num_beams)),
            image_dpi=int(os.getenv("IMAGE_DPI", defaults.image_dpi)),
            input_directory=project_root / os.getenv("INPUT_DIRECTORY", "test_images"),
            output_directory=project_root / os.getenv("OUTPUT_DIRECTORY", "outputs/text"),
            line_output_directory=project_root / os.getenv("LINE_OUTPUT_DIRECTORY", "outputs/lines"),
            debug_directory=project_root / os.getenv("DEBUG_DIRECTORY", "outputs/debug"),
            model_cache_directory=project_root / os.getenv("MODEL_CACHE_DIRECTORY", "pretrained_models"),
            log_directory=project_root / os.getenv("LOG_DIRECTORY", "logs"),
            save_line_images=os.getenv("SAVE_LINE_IMAGES", "false").lower() == "true",
        )

    def with_output_directory(self, output_directory: Path) -> "Settings":
        return replace(self, output_directory=output_directory.resolve())
