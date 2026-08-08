"""Direct shared-runtime adapter for complete-document SmartHTR recognition."""

from __future__ import annotations

import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol


@dataclass(frozen=True, slots=True)
class OCRPageResult:
    page_number: int
    text: str
    processing_time: float | None = None


@dataclass(frozen=True, slots=True)
class SmartHTROCRResult:
    status: str
    pages: tuple[OCRPageResult, ...]
    full_text: str
    metadata: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)


class SmartHTRClientError(RuntimeError):
    """Raised when the shared SmartHTR runtime cannot process a document."""


class SmartHTRClient(ABC):
    @abstractmethod
    def recognize(self, student_sheet: Path) -> SmartHTROCRResult:
        """Recognize one complete answer-sheet image or PDF."""


class _Pipeline(Protocol):
    def run(self, input_path: Path): ...


class SharedRuntimeSmartHTRClient(SmartHTRClient):
    """Calls the existing SmartHTR pipeline inside the current Python runtime.

    This adapter intentionally crosses no process or network boundary. In a
    Colab runtime, both SmartHTR and SmartEval import from the same mounted
    project checkout, so the existing pipeline and its loaded recognizer are
    reused for every student sheet handled by this client instance.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        *,
        pipeline_factory: Callable[[], _Pipeline] | None = None,
    ) -> None:
        self.project_root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        self._pipeline_factory = pipeline_factory
        self._pipeline: _Pipeline | None = None
        self._lock = threading.Lock()
        self._recognition_lock = threading.Lock()

    def recognize(self, student_sheet: Path) -> SmartHTROCRResult:
        student_sheet = student_sheet.resolve()
        if not student_sheet.is_file():
            raise SmartHTRClientError("Student answer sheet was not found.")
        try:
            # The underlying model and its GPU resources are shared by this
            # process, so complete-document recognition is intentionally
            # serialized while preserving one loaded pipeline instance.
            with self._recognition_lock:
                pipeline = self._get_pipeline()
                document = pipeline.run(student_sheet)
        except Exception as error:
            raise SmartHTRClientError("The SmartHTR pipeline could not process the student answer sheet.") from error

        pages = tuple(
            OCRPageResult(page_number=page.number, text=page.text)
            for page in sorted(document.pages, key=lambda page: page.number)
        )
        return SmartHTROCRResult(
            status="success",
            pages=pages,
            full_text=document.full_text,
            metadata={"page_count": len(pages), "model": getattr(pipeline.settings, "model_name", "")},
        )

    def _get_pipeline(self) -> _Pipeline:
        with self._lock:
            if self._pipeline is None:
                self._pipeline = self._build_pipeline()
            return self._pipeline

    def _build_pipeline(self) -> _Pipeline:
        if self._pipeline_factory is not None:
            return self._pipeline_factory()

        smarthtr_root = self.project_root / "SmartHTR"
        if not smarthtr_root.is_dir():
            raise SmartHTRClientError("The SmartHTR project directory is unavailable in this runtime.")
        if str(smarthtr_root) not in sys.path:
            sys.path.insert(0, str(smarthtr_root))
        try:
            from smarthtr.config.settings import Settings as SmartHTRSettings
            from smarthtr.pipeline.ocr_pipeline import OCRPipeline
        except ImportError as error:
            raise SmartHTRClientError("SmartHTR dependencies are unavailable in this runtime.") from error
        return OCRPipeline(SmartHTRSettings.from_environment())


class LocalSmartHTRClient(SharedRuntimeSmartHTRClient):
    """Compatibility name for the default shared-runtime SmartHTR adapter."""


def create_smarthtr_client(settings) -> SmartHTRClient:
    """Create the in-process SmartHTR provider used by SmartEval."""
    if settings.smarthr_provider not in {"local", "shared_runtime"}:
        raise ValueError("SmartEval requires SMARTHR_PROVIDER=local for the shared SmartHTR runtime.")
    return SharedRuntimeSmartHTRClient()
