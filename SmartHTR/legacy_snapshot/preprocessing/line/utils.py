"""
---------------------------------------------------------
Module    : utils.py
Project   : SmartHTR

Description:
    Utility functions for line preprocessing.
---------------------------------------------------------
"""

from __future__ import annotations

import cv2
import numpy as np


def trim_white_border(
    image: np.ndarray,
    threshold: int = 250,
) -> np.ndarray:
    """
    Remove surrounding white borders.
    """

    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY,
        )
    else:
        gray = image

    coords = cv2.findNonZero(
        255 - cv2.threshold(
            gray,
            threshold,
            255,
            cv2.THRESH_BINARY,
        )[1]
    )

    if coords is None:
        return image

    x, y, w, h = cv2.boundingRect(coords)

    return image[y:y + h, x:x + w]