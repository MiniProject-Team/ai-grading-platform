from pathlib import Path
import cv2

from smarthtr.config.settings import Settings
from smarthtr.document.loader import DocumentLoader
from smarthtr.preprocessing.image_preprocessor import ImagePreprocessor


def main():
    # Change this to your actual answer-sheet PDF
    input_pdf = Path("test_images/test.pdf")

    settings = Settings()
    loader = DocumentLoader(settings)
    preprocessor = ImagePreprocessor()

    document = loader.load(input_pdf)

    output_dir = Path("outputs/preprocessed")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SMARTHTR PREPROCESSING TEST")
    print("=" * 60)
    print(f"Input : {input_pdf}")
    print(f"Pages : {len(document.pages)}")
    print()

    for page in document.pages:
        print(f"Processing page {page.number}...")

        # Run existing SmartHTR preprocessing
        preprocessor.process(page)

        if page.processed_image is None:
            print("ERROR: processed_image was not generated")
            continue

        output_path = output_dir / f"page_{page.number:03d}_enhanced.png"

        # SmartHTR uses RGB images; OpenCV writes BGR
        image_bgr = cv2.cvtColor(
            page.processed_image,
            cv2.COLOR_RGB2BGR
        )

        success = cv2.imwrite(
            str(output_path),
            image_bgr
        )

        print(f"  Original shape : {page.image.shape}")
        print(f"  Enhanced shape : {page.processed_image.shape}")
        print(f"  Saved          : {output_path}")
        print(f"  Success        : {success}")
        print()

    print("=" * 60)
    print("PREPROCESSING TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()