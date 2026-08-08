"""Contrast and noise handling shared by page and line preprocessing."""

from __future__ import annotations

import cv2
import numpy as np


def enhance(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    denoised = cv2.fastNlMeansDenoising(gray, None, 8, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    return cv2.cvtColor(clahe, cv2.COLOR_GRAY2RGB)
