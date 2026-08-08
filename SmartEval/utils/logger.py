from __future__ import annotations

import logging

from config.settings import Settings


def configure_logging(settings: Settings) -> logging.Logger:
    settings.log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("smarteval")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for handler in (logging.StreamHandler(), logging.FileHandler(settings.log_directory / "smarteval.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
