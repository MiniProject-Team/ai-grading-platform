"""Request-local progress reporting, also visible in the evaluation log."""

from contextvars import ContextVar
import logging
from typing import Callable


progress_callback: ContextVar[Callable[[str, str], None] | None] = ContextVar("evaluation_progress", default=None)


def report_progress(stage: str, message: str) -> None:
    logging.getLogger("smarteval").info("[Progress] %s: %s", stage, message)
    callback = progress_callback.get()
    if callback is not None:
        callback(stage, message)
