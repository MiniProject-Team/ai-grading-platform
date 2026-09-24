from pathlib import Path

from smarthtr.config.settings import Settings
from smarthtr.document.loader import DocumentLoader
from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor
from smarthtr.export.preprocessed_pdf_exporter import (
    PreprocessedPdfExporter,
)


def main():
    input_pdf = Path("test_images/test.pdf")

    output_pdf = Path(
        "outputs/preprocessed/test_clahe.pdf"
    )

    settings = Settings()

    loader = DocumentLoader(settings)
    preprocessor = ImagePreprocessor()
    exporter = PreprocessedPdfExporter(
        jpeg_quality=85
    )

    print("=" * 65)
    print("SMARTHTR → PREPROCESSED PDF")
    print("=" * 65)

    document = loader.load(input_pdf)

    print(f"Pages: {len(document.pages)}")

    # Apply SmartHTR preprocessing to every page.
    for page in document.pages:
        print(f"Preprocessing page {page.number}...")
        preprocessor.process(page)

    # Create OCR-ready PDF.
    result = exporter.export(
        document,
        output_pdf,
    )

    size_mb = result.stat().st_size / (1024 * 1024)

    print()
    print("=" * 65)
    print("EXPORT COMPLETE")
    print("=" * 65)
    print(f"Output : {result}")
    print(f"Size   : {size_mb:.2f} MB")

    if size_mb >= 14:
        print()
        print("WARNING: PDF is still >= 14 MB")
    else:
        print()
        print("OK: PDF is below the 14 MB OCR limit")


if __name__ == "__main__":
    main()