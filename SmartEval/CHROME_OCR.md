Chrome OCR is a visible local Windows workflow using installed Google Chrome.
Set `OCR_PROVIDER=chrome` and `CHROME_OCR_WINDOW_MODE=simple` in `.env`.
`CHROME_OCR_EXECUTABLE` may be left empty to check standard installation locations,
or set to `C:\Program Files\Google\Chrome\Application\chrome.exe`.

Install `requirements.txt` in the shared Python environment. The added dependencies
are PyAutoGUI and pyperclip. No browser is downloaded. No dedicated profile,
remote debugging, DOM extraction, Playwright, Selenium, or pygetwindow activation
is used by this implementation.

Run from `SmartEval`, first against an existing preprocessed PDF:

```powershell
../.venv/Scripts/python.exe test_chrome_ocr.py outputs/debug/comparison/smarteval_preprocessed.pdf
```

After standalone succeeds, run preprocessing and parser integration without grading:

```powershell
../.venv/Scripts/python.exe test_chrome_ocr.py ../SmartHTR/test_images/sample.pdf --integration
```

Keep the desktop unlocked, move the pointer away from screen corners before starting,
and avoid keyboard/mouse input while copying. Adjust `CHROME_OCR_CLICK_X/Y` to a
point within the displayed PDF page. Defaults are 700/500, a ten-second initial wait,
five maximum attempts, two-second retry delay, five identical consecutive useful
copies to stabilize, and twenty minimum non-padding characters. These values are
configurable through the `CHROME_OCR_*` settings in `.env.example`.

Each attempt uses a new clipboard sentinel; the longest useful copy is retained.
Cleanup only normalizes line endings and trims outer whitespace. The original
clipboard text is restored in `finally`, before any parser invocation. Clipboard
restoration failures are reported as failures. GUI operations are serialized within
the application process; run only one local application worker using desktop OCR.
This mode does not work headlessly.

Successful diagnostics save `outputs/debug/chrome_ocr_latest.txt` and a JSON report
containing attempts, raw/cleaned counts, source PDF, executable, duration, and
clipboard restoration status. Integration additionally saves the exact parser input.
Production selection uses the existing OCR result and student text interfaces:
SmartHTR preprocesses once, then only Chrome extracts text. Chrome preprocessing
does not impose iLovePDF's upload-size limit. Generated PDFs remain under
`outputs/chrome_ocr/<run-id>/` for diagnostics; the newly opened Chrome window is closed after copying when its
Windows handle can be safely identified. Existing Chrome windows are never targeted;
remove these artifacts manually after closing their windows when no longer needed.
