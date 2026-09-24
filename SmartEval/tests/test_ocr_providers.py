from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import fitz
import httpx

from config.settings import Settings
from integration.ocr_factory import create_ocr_service
from integration.ocr_service import ILovePDFOCRService, OCRPageResult, OCRProviderError, OCRResult
from integration.smarthtr_preprocessor import PreprocessedILovePDFOCRService, SmartHTRPreprocessor
from integration.student_text_provider import SmartHTRIntegrationService, SmartHTRStudentTextProvider
from integration.smarthtr_client import TrOCROCRService


def _pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    document.new_page().insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


class OCRProviderTests(unittest.TestCase):
    def test_default_factory_selects_existing_trocr_provider(self):
        service = create_ocr_service(Settings(log_directory=Path("logs")))
        self.assertIsInstance(service, TrOCROCRService)

    def test_factory_selects_ilovepdf_provider(self):
        settings = Settings(log_directory=Path("logs"), ocr_provider="ilovepdf", ilovepdf_public_key="public", ilovepdf_secret_key="secret")
        self.assertIsInstance(create_ocr_service(settings), ILovePDFOCRService)

    def test_trocr_factory_does_not_add_preprocessing(self):
        service = create_ocr_service(Settings(log_directory=Path("logs")))
        self.assertIsInstance(service, TrOCROCRService)
        self.assertNotIsInstance(service, PreprocessedILovePDFOCRService)

    def test_missing_ilovepdf_credentials_returns_structured_error(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("Q1. Answer"))
            result = ILovePDFOCRService("", "").recognize(path)
        self.assertFalse(result.success)
        self.assertEqual(result.provider, "ilovepdf")
        self.assertIn("credentials are missing", result.error)

    def test_common_result_format_reaches_existing_downstream_provider(self):
        result = OCRResult(
            provider="ilovepdf",
            extracted_text="Q1. Same downstream text",
            pages=(OCRPageResult(1, "Q1. Same downstream text"),),
            success=True,
            status="success",
        )
        provider = SmartHTRStudentTextProvider(SmartHTRIntegrationService(_ResultClient(result)))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("input"))
            self.assertEqual(provider.get_text(path), result.extracted_text)

    def test_mocked_ilovepdf_workflow_downloads_searchable_pdf(self):
        server = "https://server.example"
        calls: list[tuple[str, str]] = []
        process_body: bytes | None = None
        result_pdf = _pdf_bytes("Q1. OCR answer")

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal process_body
            calls.append((request.method, str(request.url)))
            if request.url.path == "/v1/auth":
                return httpx.Response(200, json={"token": "test-token"})
            if request.url.path == "/v1/start/pdfocr/in":
                return httpx.Response(200, json={"server": server, "task": "task-1"})
            if request.url.path == "/v1/upload":
                return httpx.Response(200, json={"server_filename": "uploaded.pdf"})
            if request.url.path == "/v1/process":
                process_body = request.content
                return httpx.Response(200, json={"status": "TaskCompleted"})
            if request.url.path == "/v1/download/task-1":
                return httpx.Response(200, content=result_pdf)
            return httpx.Response(404)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("input"))
            client = httpx.Client(transport=httpx.MockTransport(handler))
            result = ILovePDFOCRService("public", "secret", http_client=client).recognize(path)
            client.close()

        self.assertTrue(result.success)
        self.assertEqual(result.provider, "ilovepdf")
        self.assertEqual(result.extracted_text, "Q1. OCR answer")
        self.assertEqual(result.metadata["ocr_languages"], ["eng"])
        assert process_body is not None
        self.assertIn(b"ocr_languages%5B0%5D=eng", process_body)
        self.assertNotIn(b"ocr_languages%5B%5D=eng", process_body)
        self.assertEqual([path for _, path in calls], [
            "https://api.ilovepdf.com/v1/auth",
            "https://api.ilovepdf.com/v1/start/pdfocr/in",
            "https://server.example/v1/upload",
            "https://server.example/v1/process",
            "https://server.example/v1/download/task-1",
        ])

    def test_ilovepdf_preprocesses_and_cleans_temporary_pdf(self):
        result = OCRResult(provider="ilovepdf", extracted_text="answer", success=True, status="success")
        delegate = _RecordingOCRService(result)
        preprocessor = _WritingPreprocessor()
        service = PreprocessedILovePDFOCRService(delegate, preprocessor)

        with TemporaryDirectory() as directory:
            original = Path(directory) / "answer.pdf"
            original_bytes = _pdf_bytes("original")
            original.write_bytes(original_bytes)
            returned = service.recognize(original)
            passed_path = delegate.paths[0]
            self.assertTrue(passed_path.name.startswith("preprocessed"))
            self.assertFalse(passed_path.exists())
            self.assertEqual(original.read_bytes(), original_bytes)

        self.assertIs(returned, result)
        self.assertEqual(preprocessor.inputs, [original.resolve()])

    def test_preprocessing_failure_is_structured_ilovepdf_failure(self):
        delegate = _RecordingOCRService(OCRResult(provider="ilovepdf", success=True, status="success"))
        service = PreprocessedILovePDFOCRService(delegate, _FailingPreprocessor())

        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("original"))
            result = service.recognize(path)

        self.assertFalse(result.success)
        self.assertEqual(result.provider, "ilovepdf")
        self.assertIn("SmartHTR preprocessing failed", result.error)
        self.assertEqual(delegate.paths, [])

    def test_preprocessor_retries_lower_jpeg_quality_until_under_limit(self):
        loader = _FakeLoader()
        exporter = _SizedExporter({85: 14 * 1024 * 1024, 80: 13 * 1024 * 1024})
        preprocessor = SmartHTRPreprocessor(
            loader_factory=lambda _: loader,
            preprocessor_factory=lambda: _FakeImagePreprocessor(),
            exporter_factory=lambda quality: exporter.for_quality(quality),
        )

        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("original"))
            output = preprocessor.preprocess(path, Path(directory) / "temp")

        self.assertEqual(output.name, "student-preprocessed-80.pdf")
        self.assertEqual(loader.loaded, path.resolve())
        self.assertEqual(exporter.qualities, [85, 80])

    def test_preprocessor_reports_upload_limit_when_all_qualities_are_too_large(self):
        exporter = _SizedExporter({quality: 14 * 1024 * 1024 for quality in (85, 80, 75, 70)})
        preprocessor = SmartHTRPreprocessor(
            loader_factory=lambda _: _FakeLoader(),
            preprocessor_factory=lambda: _FakeImagePreprocessor(),
            exporter_factory=lambda quality: exporter.for_quality(quality),
        )

        with TemporaryDirectory() as directory:
            path = Path(directory) / "answer.pdf"
            path.write_bytes(_pdf_bytes("original"))
            with self.assertRaisesRegex(OCRProviderError, "could not reduce.*14 MB"):
                preprocessor.preprocess(path, Path(directory) / "temp")


class _ResultClient:
    def __init__(self, result: OCRResult) -> None:
        self.result = result

    def recognize(self, path: Path) -> OCRResult:
        return self.result


class _RecordingOCRService:
    def __init__(self, result: OCRResult) -> None:
        self.result = result
        self.paths: list[Path] = []

    def recognize(self, path: Path) -> OCRResult:
        self.paths.append(path)
        return self.result


class _WritingPreprocessor:
    def __init__(self) -> None:
        self.inputs: list[Path] = []

    def preprocess(self, input_path: Path, output_directory: Path) -> Path:
        self.inputs.append(input_path.resolve())
        output = output_directory / "preprocessed.pdf"
        output.write_bytes(b"preprocessed")
        return output


class _FailingPreprocessor:
    def preprocess(self, input_path: Path, output_directory: Path) -> Path:
        raise OCRProviderError("SmartHTR preprocessing failed: test failure")


class _FakeLoader:
    def __init__(self) -> None:
        self.loaded: Path | None = None
        self.document = type("Document", (), {"pages": [_FakePage()]})()

    def load(self, path: Path):
        self.loaded = path.resolve()
        return self.document


class _FakeImagePreprocessor:
    def process(self, page) -> None:
        page.processed = True


class _FakePage:
    pass


class _SizedExporter:
    def __init__(self, sizes: dict[int, int]) -> None:
        self.sizes = sizes
        self.qualities: list[int] = []

    def for_quality(self, quality: int):
        self.qualities.append(quality)
        return self

    def export(self, document, output_path: Path) -> Path:
        output_path.write_bytes(b"x" * self.sizes[self.qualities[-1]])
        return output_path


if __name__ == "__main__":
    unittest.main()