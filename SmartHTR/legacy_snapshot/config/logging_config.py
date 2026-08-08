"""
---------------------------------------------------------
Module    : logging_config.py
Project   : SmartHTR
Author    : Ayush Bire

Description:
    Centralized logging configuration.
---------------------------------------------------------
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.paths import LOGS_DIR
from config.settings import settings


LOGGER_NAME = "SmartHTR"


def configure_logging() -> logging.Logger:
    """
    Configure application logging.

    Returns
    -------
    logging.Logger
        Configured application logger.
    """

    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(settings.logging.level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_file: Path = LOGS_DIR / "application.log"

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


logger = configure_logging()