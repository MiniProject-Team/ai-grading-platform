from pathlib import Path

import cv2
import numpy as np

from smarthtr.config.settings import Settings
from smarthtr.document.loader import DocumentLoader


def clahe_variant(image: np.ndarray) -> np.ndarray:
    """Current-style grayscale + CLAHE preprocessing."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        h=8,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(denoised)

    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)


def background_normalized_variant(image: np.ndarray) -> np.ndarray:
    """
    Reduce large-scale illumination/background variation
    while preserving handwriting.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Estimate slowly varying background.
    background = cv2.GaussianBlur(
        gray,
        (0, 0),
        sigmaX=25,
    )

    # Normalize illumination.
    normalized = cv2.divide(
        gray,
        background,
        scale=255,
    )

    normalized = np.clip(normalized, 0, 255).astype(np.uint8)

    # Mild denoising.
    normalized = cv2.fastNlMeansDenoising(
        normalized,
        None,
        h=6,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    # Mild contrast enhancement.
    clahe = cv2.createCLAHE(
        clipLimit=1.5,
        tileGridSize=(8, 8),
    )

    normalized = clahe.apply(normalized)

    return cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)


def adaptive_threshold_variant(image: np.ndarray) -> np.ndarray:
    """
    Strong black/white separation for OCR experimentation.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    gray = cv2.fastNlMeansDenoising(
        gray,
        None,
        h=6,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    # Improve local contrast first.
    clahe = cv2.createCLAHE(
        clipLimit=1.5,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(gray)

    thresholded = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # Keep output RGB so it matches SmartHTR's convention.
    return cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)


def save_rgb(image: np.ndarray, path: Path) -> None:
    """Save an RGB image correctly using OpenCV."""
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)


def main() -> None:
    input_pdf = Path("test_images/test.pdf")

    output_dir = Path("outputs/preprocessing_variants")
    output_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings()
    loader = DocumentLoader(settings)

    document = loader.load(input_pdf)

    # Only use page 1 for this experiment.
    page = document.pages[0]
    original = page.image

    print("=" * 65)
    print("SMARTHTR PREPROCESSING VARIANT EXPERIMENT")
    print("=" * 65)
    print(f"Input : {input_pdf}")
    print(f"Page  : {page.number}")
    print(f"Shape : {original.shape}")
    print()

    variants = {
        "original": original,
        "clahe": clahe_variant(original),
        "background_normalized": background_normalized_variant(original),
        "adaptive_threshold": adaptive_threshold_variant(original),
    }

    for name, image in variants.items():
        output_path = output_dir / f"page_001_{name}.png"

        save_rgb(image, output_path)

        print(f"[OK] {name}")
        print(f"     {output_path}")
        print(f"     shape = {image.shape}")
        print()

    print("=" * 65)
    print("EXPERIMENT COMPLETE")
    print("=" * 65)
if __name__ == "__main__":
    main()