"""Visible installed-Chrome PDF copying for the local Windows prototype."""
from __future__ import annotations

from app.progress import report_progress

from importlib import import_module
import logging
import os
from pathlib import Path
import subprocess
import threading
import time
from uuid import uuid4

import fitz

from config.settings import Settings
from .ocr_service import OCRProviderError, OCRResult, OCRService
from .chrome_window import ChromeWindowTracker


class ChromeOCRService(OCRService):
    # Keyboard and clipboard are shared by every request in this process.
    _desktop_lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("smarteval")

    def executable(self) -> Path:
        configured = self.settings.chrome_ocr_executable.strip()
        candidates = [Path(configured)] if configured else [
            Path(os.environ.get(root, default)) / "Google/Chrome/Application/chrome.exe"
            for root, default in (("PROGRAMFILES", "C:/Program Files"),
                                  ("PROGRAMFILES(X86)", "C:/Program Files (x86)"),
                                  ("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
        ]
        for path in candidates:
            if path.is_file():
                return path.resolve()
        raise OCRProviderError("Installed Google Chrome executable missing. Set CHROME_OCR_EXECUTABLE.")

    def recognize(self, input_path: Path) -> OCRResult:
        with self._desktop_lock:
            return self._recognize(input_path)

    def _recognize(self, input_path: Path) -> OCRResult:
        started = time.perf_counter()
        path = input_path.resolve()
        counts: list[int] = []
        metadata = {"source_pdf": str(path), "attempt_character_counts": counts,
                    "clipboard_restored": False, "raw_character_count": 0,
                    "returned_character_count": 0}
        best = ""
        error = None
        pages = 0
        clipboard = None
        captured = False
        window = None
        warnings = []
        try:
            try:
                clipboard = import_module("pyperclip")
            except ImportError as exc:
                raise OCRProviderError("pyperclip unavailable; install SmartEval requirements.") from exc
            original = clipboard.paste()
            captured = True
            try:
                gui = import_module("pyautogui")
            except ImportError as exc:
                raise OCRProviderError("pyautogui unavailable; install SmartEval requirements.") from exc
            s = self.settings
            if s.chrome_ocr_window_mode != "simple":
                raise OCRProviderError("CHROME_OCR_WINDOW_MODE must be simple.")
            if min(s.chrome_ocr_max_attempts, s.chrome_ocr_stable_attempts, s.chrome_ocr_min_characters) < 1:
                raise OCRProviderError("Chrome attempt counts and minimum characters must be positive.")
            if min(s.chrome_ocr_initial_wait_seconds, s.chrome_ocr_retry_delay_seconds) < 0:
                raise OCRProviderError("Chrome wait durations cannot be negative.")
            if not path.is_file() or path.suffix.lower() != ".pdf":
                raise OCRProviderError(f"Processed PDF missing or not a PDF: {path}")
            with fitz.open(path) as document:
                pages = document.page_count
            executable = self.executable()
            metadata["executable"] = str(executable)
            self.logger.info("[Chrome OCR] Opening processed PDF: %s", path)
            report_progress("reading", "Opening the preprocessed PDF for handwriting recognition.")
            window = ChromeWindowTracker()
            try:
                subprocess.Popen([str(executable), "--new-window", path.as_uri()])
            except OSError as exc:
                raise OCRProviderError(f"Chrome failed to launch: {exc}") from exc
            time.sleep(s.chrome_ocr_initial_wait_seconds)
            window.capture()
            previous = None
            stable = 0
            changed = False
            for attempt in range(s.chrome_ocr_max_attempts):
                gui.click(s.chrome_ocr_click_x, s.chrome_ocr_click_y)
                time.sleep(0.3)
                sentinel = "__SMARTEVAL_CHROME_OCR_WAITING__" + uuid4().hex
                clipboard.copy(sentinel)
                gui.hotkey("ctrl", "a")
                time.sleep(0.3)
                gui.hotkey("ctrl", "c")
                time.sleep(0.5)
                copied = clipboard.paste()
                changed |= copied != sentinel
                text = copied if copied != sentinel else ""
                counts.append(len(text))
                self.logger.info("[Chrome OCR] Attempt %s: %s chars", attempt + 1, len(text))
                report_progress("reading", f"OCR reading attempt {attempt + 1}: {len(text):,} characters extracted.")
                useful = len(text.strip()) >= s.chrome_ocr_min_characters
                if useful and len(text) > len(best):
                    best = text
                stable = stable + 1 if useful and text == previous else (1 if useful else 0)
                previous = text
                if stable >= s.chrome_ocr_stable_attempts and text == best:
                    break
                if attempt + 1 < s.chrome_ocr_max_attempts:
                    time.sleep(s.chrome_ocr_retry_delay_seconds)
            if not best:
                reason = "clipboard never changed" if not changed else (
                    "copied text empty" if not any(counts) else "copied result below minimum character threshold")
                raise OCRProviderError(f"Chrome OCR failed: {reason}. Check viewer click coordinates and wait settings.")
        except Exception as exc:
            error = str(exc)
        finally:
            if window is not None:
                try:
                    metadata["window_close_requested"] = window.close()
                    if not metadata["window_close_requested"]:
                        warnings.append("Chrome window could not be safely identified for closing; left open.")
                except Exception as exc:
                    warnings.append(f"Unable to close OCR Chrome window: {exc}")
            if captured:
                try:
                    clipboard.copy(original)
                    metadata["clipboard_restored"] = True
                except Exception as exc:
                    error = f"{error or 'Chrome OCR completed'}; clipboard restoration failed: {exc}"
        cleaned = best.replace("\r\n", "\n").replace("\r", "\n").strip()
        metadata.update(raw_character_count=len(best), returned_character_count=len(cleaned))
        self.logger.info("[Chrome OCR] RAW CHROME CHAR COUNT: %s; RETURNED/CLEANED CHAR COUNT: %s", len(best), len(cleaned))
        return OCRResult(provider="chrome", extracted_text=cleaned, pages_processed=pages,
                         processing_time=time.perf_counter() - started, success=error is None,
                         error=error, metadata=metadata,
                         warnings=tuple(warnings))
