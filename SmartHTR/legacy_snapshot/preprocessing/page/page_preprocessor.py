"""
---------------------------------------------------------
Module    : page_preprocessor.py
Project   : SmartHTR

Description:
    Coordinates all page preprocessing steps.
---------------------------------------------------------
"""

from __future__ import annotations

from core.entities import Page

from .border_removal import BorderRemovalProcessor
from .contrast import ContrastProcessor
from .denoise import DenoiseProcessor
from .deskew import DeskewProcessor
from .resize import ResizeProcessor
from .shadow_removal import ShadowRemovalProcessor


class PagePreprocessor:
    """
    Executes all page preprocessing stages.
    """

    def __init__(self) -> None:

        self.processors = [

            ResizeProcessor(),

            DeskewProcessor(),

            ShadowRemovalProcessor(),

            ContrastProcessor(),

            DenoiseProcessor(),

            BorderRemovalProcessor(),

        ]

    def process(
        self,
        page: Page,
    ) -> None:
        """
        Apply all preprocessing steps to a page.
        """

        for processor in self.processors:

            processor.process(page)