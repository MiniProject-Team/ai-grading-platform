from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from integration.smarthtr_client import SharedRuntimeSmartHTRClient


@dataclass
class _Page:
    number: int
    text: str


@dataclass
class _Document:
    pages: list[_Page]

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in sorted(self.pages, key=lambda page: page.number))


class _Pipeline:
    class _Settings:
        model_name = "microsoft/trocr-small-handwritten"

    settings = _Settings()

    def __init__(self) -> None:
        self.calls: list[Path] = []

    def run(self, input_path: Path) -> _Document:
        self.calls.append(input_path)
        return _Document([_Page(2, "Q2. Second answer"), _Page(1, "Q1. First answer")])


class SharedRuntimeSmartHTRClientTests(unittest.TestCase):
    def test_adapts_ordered_complete_document_text_and_reuses_pipeline(self):
        with TemporaryDirectory() as directory:
            sheet = Path(directory) / "student.pdf"
            sheet.write_bytes(b"%PDF-1.4 test")
            pipeline = _Pipeline()
            builds = 0

            def build_pipeline():
                nonlocal builds
                builds += 1
                return pipeline

            client = SharedRuntimeSmartHTRClient(pipeline_factory=build_pipeline)
            first = client.recognize(sheet)
            second = client.recognize(sheet)

        self.assertEqual(builds, 1)
        self.assertEqual(len(pipeline.calls), 2)
        self.assertEqual([page.page_number for page in first.pages], [1, 2])
        self.assertEqual(first.full_text, "Q1. First answer\n\nQ2. Second answer")
        self.assertEqual(first.metadata["model"], "microsoft/trocr-small-handwritten")
        self.assertEqual(second.full_text, first.full_text)

    def test_missing_sheet_is_rejected_before_pipeline_creation(self):
        client = SharedRuntimeSmartHTRClient(pipeline_factory=lambda: self.fail("pipeline should not be built"))
        with self.assertRaisesRegex(Exception, "Student answer sheet was not found"):
            client.recognize(Path("missing-student-sheet.pdf"))
