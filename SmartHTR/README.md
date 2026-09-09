# SmartHTR

SmartHTR is a modular full-page handwritten text recognition engine. It accepts a scanned image or PDF, detects text regions across every page, recognizes each cropped line, reconstructs natural reading order, and writes complete page text files. It is designed as an independent OCR engine for later use by SmartEval; it contains no grading or answer-evaluation logic.

## Architecture

`DocumentLoader -> ImagePreprocessor -> DocTRDetector -> LineCropper -> LinePreprocessor -> Recognizer -> ReadingOrderReconstructor -> TextExporter`

DocTR is used only for text/line detection. `TrOCRSmallRecognizer` is the current handwritten-recognition baseline, configured with TrOCR Base, and implements the `Recognizer` interface, so a fine-tuned model, TrOCR Large on a GPU machine, or a future SmartHTR recognizer can replace it without changing the pipeline.

## Installation

Use Python 3.10 on Windows 11 for the supported local baseline. Create a virtual environment, activate it, and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The first run downloads DocTR and `microsoft/trocr-base-handwritten` into `pretrained_models/`.

## Local execution

```powershell
python main.py --input test_images/page003.jpg
python main.py --input test_images/sample.pdf
```

Text is written per page to `outputs/text/page_001.txt`, `page_002.txt`, and so on. Set `SAVE_LINE_IMAGES=true` in `.env` to save processed crops under `outputs/lines/` for inspection.

## Configuration

Configuration lives in `smarthtr/config/settings.py` and can be overridden in `.env`:

```text
MODEL_NAME=microsoft/trocr-base-handwritten
DEVICE=auto
MAX_NEW_TOKENS=128
NUM_BEAMS=5
IMAGE_DPI=300
```

`DEVICE=auto` uses CUDA when it is available and otherwise runs on CPU. The core pipeline contains no Colab-specific logic.

## VS Code notebooks and Colab

The notebooks in `notebooks/` are small experiment entry points. Open them in VS Code and connect a notebook kernel to a Colab GPU runtime where your VS Code/Colab setup supports it. They import `smarthtr` modules rather than duplicating the OCR implementation. Use the same configuration with `DEVICE=cuda` when the connected runtime provides CUDA.

## Current limitations

This is a baseline using TrOCR Base. It has not been fine-tuned on a SmartHTR dataset, and handwriting accuracy depends on scan quality, layout, detection quality, and the underlying pretrained model. Full A4 pages are processed automatically, but CPU processing on an 8 GB laptop can take time.

## Future work

When a labelled handwriting dataset is available, training will be added as a separate workflow. SmartEval can call this engine and consume document pages and `full_text`; it will remain separate from marks, feedback, semantic matching, and answer mapping.
