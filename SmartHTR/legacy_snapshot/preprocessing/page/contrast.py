"""Improve page contrast while preserving RGB images."""

from __future__ import annotations

import cv2

from core.entities import Page


class ContrastProcessor:
    """Enhance page contrast using CLAHE."""

    def __init__(
        self,
        clip_limit: float = 2.0,
        tile_grid_size: tuple[int, int] = (8, 8),
    ) -> None:
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size

    def process(self, page: Page) -> None:
        image = page.image
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        clahe = cv2.createCLAHE(
            clipLimit=self.clip_limit,
            tileGridSize=self.tile_grid_size,
        )
        enhanced = clahe.apply(image)
        page.processed_image = cv2.cvtColor(
            enhanced,
            cv2.COLOR_GRAY2RGB,
        )
        page.metadata.add(
            "contrast",
            {
                "applied": True,
                "method": "CLAHE",
                "clip_limit": self.clip_limit,
                "tile_grid": self.tile_grid_size,
            },
        )
