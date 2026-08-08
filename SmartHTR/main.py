from __future__ import annotations

import argparse
import sys
from pathlib import Path

from smarthtr.config.settings import Settings
from smarthtr.pipeline.ocr_pipeline import OCRPipeline
from smarthtr.utils.logger import configure_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full-page handwritten OCR.")
    parser.add_argument("--input", required=True, type=Path, help="Image or PDF to process")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for page text files")
    args = parser.parse_args()

    settings = Settings.from_environment()
    if args.output_dir is not None:
        settings = settings.with_output_directory(args.output_dir)
    logger = configure_logging(settings)

    try:
        result = OCRPipeline(settings=settings).run(args.input)
    except Exception as error:
        logger.exception("OCR failed for %s", args.input)
        print(f"OCR failed: {error}", file=sys.stderr)
        return 1

    print(f"OCR completed: {len(result.pages)} page(s) written to {settings.output_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
