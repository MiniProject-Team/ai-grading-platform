from __future__ import annotations

import logging

from smarteval.config.settings import Settings


def configure_logging(settings: Settings) -> logging.Logger:
    logger = logging.getLogger("smarteval")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(settings.log_directory / "smarteval.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
