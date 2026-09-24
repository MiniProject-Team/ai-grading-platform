"""Provider-neutral OCR contracts and the iLovePDF PDF OCR adapter."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import fitz
import httpx


@dataclass(frozen=True, slots=True)
class OCRPageResult:
    page_number: int
    text: str
    processing_time: float | None = None


@dataclass(frozen=True, slots=True, init=False)
class OCRResult:
    provider: str
    extracted_text: str
    pages_processed: int
    processing_time: float | None
    success: bool
    error: str | None
    metadata: dict[str, object]
    pages: tuple[OCRPageResult, ...]
    warnings: tuple[str, ...]
    status: str

    def __init__(
        self,
        provider: str = "trocr",
        extracted_text: str = "",
        pages_processed: int = 0,
        processing_time: float | None = None,
        success: bool = True,
        error: str | None = None,
        metadata: dict[str, object] | None = None,
        pages: tuple[OCRPageResult, ...] = (),
        warnings: tuple[str, ...] = (),
        status: str | None = None,
        full_text: str | None = None,
    ) -> None:
        text = extracted_text if full_text is None else full_text
        resolved_status = status or ("success" if success else "failed")
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "extracted_text", text)
        object.__setattr__(self, "pages_processed", pages_processed or len(pages))
        object.__setattr__(self, "processing_time", processing_time)
        object.__setattr__(self, "success", success and resolved_status != "failed")
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "metadata", metadata or {})
        object.__setattr__(self, "pages", pages)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "status", resolved_status)

    @property
    def full_text(self) -> str:
        return self.extracted_text


class OCRService(ABC):
    @abstractmethod
    def recognize(self, input_path: Path) -> OCRResult:
        """Recognize one complete document without exposing provider details."""


class OCRProviderError(RuntimeError):
    """An expected provider failure that can be shown as a structured OCR error."""


class ILovePDFOCRService(OCRService):
    """Execute iLovePDF's START -> UPLOAD -> PROCESS -> DOWNLOAD workflow."""

    _AUTH_URL = "https://api.ilovepdf.com/v1/auth"

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        region: str = "in",
        timeout: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.public_key = public_key.strip()
        self.secret_key = secret_key.strip()
        self.region = region.strip().lower() or "in"
        self.timeout = timeout
        self.http_client = http_client
        self._owned_http_client = httpx.Client(timeout=timeout) if http_client is None else None
        self.logger = logging.getLogger("smarteval")

    def recognize(self, input_path: Path) -> OCRResult:
        started = time.perf_counter()
        try:
            path = input_path.resolve()
            self._validate_pdf(path)
            if not self.public_key or not self.secret_key:
                raise OCRProviderError("iLovePDF credentials are missing. Set ILOVEPDF_PUBLIC_KEY and ILOVEPDF_SECRET_KEY.")
            self.logger.info("[OCR] Provider: ilovepdf")
            token = self._authenticate()
            task = self._start_task(token)
            server_filename = self._upload(task["server"], task["task"], token, path)
            self._process(task["server"], task["task"], token, server_filename, path.name)
            result_pdf = self._download(task["server"], task["task"], token)
            pages, text = self._extract_text(result_pdf)
            if not text:
                raise OCRProviderError("iLovePDF completed, but the downloaded PDF contained no OCR text.")
            return OCRResult(
                provider="ilovepdf",
                extracted_text=text,
                pages_processed=len(pages),
                processing_time=time.perf_counter() - started,
                success=True,
                metadata={"tool": "pdfocr", "region": self.region, "ocr_languages": ["eng"]},
                pages=tuple(pages),
            )
        except OCRProviderError as error:
            return self._failure(str(error), started)
        except httpx.TimeoutException:
            return self._failure("iLovePDF request timed out.", started)
        except httpx.HTTPError:
            return self._failure("A network error occurred while contacting iLovePDF.", started)
        except (OSError, ValueError, fitz.FileDataError) as error:
            return self._failure(f"Unable to process the PDF for iLovePDF: {error}", started)

    def _validate_pdf(self, path: Path) -> None:
        if not path.is_file():
            raise OCRProviderError(f"Input PDF was not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise OCRProviderError("iLovePDF OCR accepts PDF input only.")
        try:
            with fitz.open(path) as document:
                if document.page_count == 0:
                    raise OCRProviderError("The input PDF contains no pages.")
        except fitz.FileDataError as error:
            raise OCRProviderError("The input PDF is invalid or damaged.") from error

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        client = self.http_client or self._owned_http_client
        if client is None:
            raise OCRProviderError("iLovePDF HTTP client is unavailable.")
        return client.request(method, url, timeout=self.timeout, **kwargs)

    def _authenticate(self) -> str:
        self.logger.info("[OCR] Authenticating with iLovePDF")
        response = self._request("POST", self._AUTH_URL, json={"public_key": self.public_key, "secret_key": self.secret_key})
        if response.status_code >= 400:
            raise OCRProviderError("iLovePDF authentication failed. Check credentials and account limits.")
        token = response.json().get("token")
        if not token:
            raise OCRProviderError("iLovePDF authentication returned no JWT token.")
        return str(token)

    def _start_task(self, token: str) -> dict[str, str]:
        self.logger.info("[OCR] Starting PDF OCR task")
        response = self._request(
            "GET",
            f"https://api.ilovepdf.com/v1/start/pdfocr/{self.region}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code >= 400:
            raise OCRProviderError("iLovePDF could not start the PDF OCR task. Check the region and account limits.")
        payload = response.json()
        if not payload.get("server") or not payload.get("task"):
            raise OCRProviderError("iLovePDF returned an invalid PDF OCR task.")
        server = str(payload["server"]).strip()
        if not urlparse(server).scheme:
            server = f"https://{server}"
        return {"server": server.rstrip("/"), "task": str(payload["task"])}

    def _upload(self, server: str, task: str, token: str, path: Path) -> str:
        response = self._request(
            "POST",
            f"{server}/v1/upload",
            headers={"Authorization": f"Bearer {token}"},
            data={"task": task},
            files={"file": (path.name, path.read_bytes(), "application/pdf")},
        )
        if response.status_code >= 400:
            raise OCRProviderError("iLovePDF PDF upload failed.")
        filename = response.json().get("server_filename")
        if not filename:
            raise OCRProviderError("iLovePDF upload returned no server filename.")
        self.logger.info("[OCR] Upload successful")
        return str(filename)

    def _process(self, server: str, task: str, token: str, server_filename: str, filename: str) -> None:
        self.logger.info("[OCR] Processing PDF")
        response = self._request(
            "POST",
            f"{server}/v1/process",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "task": task,
                "tool": "pdfocr",
                "files[0][server_filename]": server_filename,
                "files[0][filename]": filename,
                "ocr_languages[0]": "eng",
            },
        )
        if response.status_code >= 400:
            detail = response.text[:300].replace("\n", " ").strip()
            suffix = f" Details: {detail}" if detail else ""
            raise OCRProviderError(f"iLovePDF PDF OCR processing failed (HTTP {response.status_code}).{suffix}")

    def _download(self, server: str, task: str, token: str) -> bytes:
        response = self._request(
            "GET",
            f"{server}/v1/download/{task}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code >= 400 or not response.content:
            raise OCRProviderError("iLovePDF PDF OCR result download failed.")
        self.logger.info("[OCR] Download successful")
        return response.content

    def _extract_text(self, pdf_bytes: bytes) -> tuple[list[OCRPageResult], str]:
        self.logger.info("[OCR] Extracting text")
        pages: list[OCRPageResult] = []
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            for number, page in enumerate(document, 1):
                pages.append(OCRPageResult(number, page.get_text().strip()))
        text = "\n\n".join(page.text for page in pages if page.text).strip()
        self.logger.info("[OCR] Extracted characters: %s", len(text))
        return pages, text

    @staticmethod
    def _failure(message: str, started: float) -> OCRResult:
        return OCRResult(
            provider="ilovepdf",
            processing_time=time.perf_counter() - started,
            success=False,
            error=message,
            status="failed",
        )