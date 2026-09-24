from pathlib import Path

import cv2
import fitz

from smarthtr.config.settings import Settings
from smarthtr.document.loader import DocumentLoader
from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor


def main():
    input_pdf = Path("test_images/test.pdf")
    output_pdf = Path("outputs/preprocessed/test_clahe.pdf")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    settings = Settings()
    loader = DocumentLoader(settings)
    preprocessor = ImagePreprocessor()

    document = loader.load(input_pdf)

    print("=" * 65)
    print("CREATING A4 PREPROCESSED PDF")
    print("=" * 65)
    print(f"Input : {input_pdf}")
    print(f"Pages : {len(document.pages)}")
    print()

    output_document = fitz.open()

    # A4 size in PDF points: 595 x 842
    A4_WIDTH = 595
    A4_HEIGHT = 842

    for page in document.pages:
        print(f"Processing page {page.number}...")

        # Existing SmartHTR preprocessing:
        # deskew + denoise + CLAHE
        preprocessor.process(page)

        if page.processed_image is None:
            raise RuntimeError(
                f"Preprocessing failed for page {page.number}"
            )

        image = page.processed_image

        # RGB -> BGR for OpenCV
        image_bgr = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2BGR
        )

        # JPEG keeps the PDF small while preserving handwriting.
        success, encoded = cv2.imencode(
            ".jpg",
            image_bgr,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                90,
                cv2.IMWRITE_JPEG_OPTIMIZE,
                1,
            ],
        )

        if not success:
            raise RuntimeError(
                f"Could not encode page {page.number}"
            )

        # Normal A4 PDF page.
        pdf_page = output_document.new_page(
            width=A4_WIDTH,
            height=A4_HEIGHT,
        )

        # Put the complete enhanced image inside the A4 page.
        pdf_page.insert_image(
            fitz.Rect(
                0,
                0,
                A4_WIDTH,
                A4_HEIGHT,
            ),
            stream=encoded.tobytes(),
            keep_proportion=True,
        )

        print(
            f"  Source image : {image.shape[1]} x {image.shape[0]}"
        )
        print(
            f"  PDF page     : A4 ({A4_WIDTH} x {A4_HEIGHT})"
        )

    output_document.save(
        output_pdf,
        deflate=True,
        garbage=4,
        clean=True,
    )

    output_document.close()

    size_mb = output_pdf.stat().st_size / (1024 * 1024)

    print()
    print("=" * 65)
    print("PREPROCESSED A4 PDF CREATED")
    print("=" * 65)
    print(f"File   : {output_pdf}")
    print(f"Exists : {output_pdf.exists()}")
    print(f"Size   : {size_mb:.2f} MB")


if __name__ == "__main__":
    main()