"""Conservative deskewing for complete page images."""

from __future__ import annotations

import cv2
import numpy as np


def deskew(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    coords = np.column_stack(np.where(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] > 0))
    if len(coords) < 20:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    angle = 90 + angle if angle < -45 else angle
    if abs(angle) < 0.2 or abs(angle) > 15:
        return image
    matrix = cv2.getRotationMatrix2D((image.shape[1] // 2, image.shape[0] // 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
