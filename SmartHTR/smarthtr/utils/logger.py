"""Application logging setup."""

from __future__ import annotations

import logging

from smarthtr.config.settings import Settings


def configure_logging(settings: Settings) -> logging.Logger:
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("smarthtr")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(settings.log_directory / "smarthtr.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
