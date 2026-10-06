"""Standalone diagnostic; --integration preprocesses an original PDF once, without grading."""
from dataclasses import replace
import argparse
import json
import logging
from pathlib import Path

from config.settings import Settings
from integration.chrome_ocr_service import ChromeOCRService
from integration.ocr_factory import create_ocr_service
from integration.student_text_provider import SmartHTRIntegrationService, SmartHTRStudentTextProvider
from parsers.student_answer_parser import StudentAnswerParser
from services.input_manager import InputManager


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--integration", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = replace(Settings.from_environment(), ocr_provider="chrome")
    debug = settings.output_directory / "debug"
    debug.mkdir(parents=True, exist_ok=True)
    service = create_ocr_service(settings) if args.integration else ChromeOCRService(settings)
    provider = SmartHTRStudentTextProvider(SmartHTRIntegrationService(service))
    try:
        text = InputManager(student_provider=provider).load_student_text(args.pdf)
    except Exception as error:
        print(f"FAILED: {error}")
        if provider.last_result:
            print(json.dumps(provider.last_result.metadata, indent=2))
        return 1
    result = provider.last_result
    report = dict(result.metadata, duration=result.processing_time, provider=result.provider)
    (debug / "chrome_ocr_latest.txt").write_text(text, encoding="utf-8")
    (debug / "chrome_ocr_latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ORIGINAL PDF:", report.get("original_pdf", "not used (standalone)"))
    print("PREPROCESSED PDF:", report["source_pdf"])
    print("OCR PROVIDER: chrome")
    print("CHROME ATTEMPTS:", report["attempt_character_counts"])
    print("RAW CHROME CHARACTERS:", report["raw_character_count"])
    print("RETURNED CHARACTERS:", len(text))
    print("CLIPBOARD RESTORED:", report["clipboard_restored"])
    if args.integration:
        assert text == result.extracted_text
        (debug / "latest_student_parser_input.txt").write_text(text, encoding="utf-8")
        print("PARSER INPUT CHARACTERS:", len(text))
        answers = StudentAnswerParser().parse(text)
        print("PARSED ANSWERS:", len(answers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
