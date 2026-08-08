"""Full-page preprocessing before DocTR detection."""

from __future__ import annotations

from smarthtr.core.entities import Page

from .deskew import deskew
from .enhancement import enhance


class ImagePreprocessor:
    def process(self, page: Page) -> Page:
        page.processed_image = enhance(deskew(page.original_image))
        return page
