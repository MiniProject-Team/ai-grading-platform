from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile

from .errors import APIProblem


class UploadWorkspace:
    def __init__(self, root: Path, keep_files: bool, evaluation_id: str) -> None:
        self.root = root
        self.keep_files = keep_files
        self.evaluation_id = evaluation_id
        self.path: Path | None = None

    def __enter__(self) -> "UploadWorkspace":
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix=f"{self.evaluation_id}_", dir=self.root))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.path and self.path.exists() and not self.keep_files:
            shutil.rmtree(self.path, ignore_errors=True)


class UploadStorage:
    _SIGNATURES = {
        ".pdf": b"%PDF-",
        ".png": b"\x89PNG\r\n\x1a\n",
    }
    _ALLOWED_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg"})

    def __init__(self, maximum_size_mb: int) -> None:
        if maximum_size_mb < 1:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be at least 1")
        self.maximum_bytes = maximum_size_mb * 1024 * 1024

    async def save(self, upload: UploadFile, destination_directory: Path, field_name: str) -> Path:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in self._ALLOWED_SUFFIXES:
            raise APIProblem(400, "UNSUPPORTED_FILE_TYPE", f"{self._label(field_name)} must be a PDF, PNG, JPG, or JPEG file.")
        destination = destination_directory / f"{field_name}{suffix}"
        size = 0
        first_chunk = b""
        try:
            with destination.open("wb") as output_file:
                while chunk := await upload.read(64 * 1024):
                    if not first_chunk:
                        first_chunk = chunk
                    size += len(chunk)
                    if size > self.maximum_bytes:
                        raise APIProblem(413, "FILE_TOO_LARGE", f"{self._label(field_name)} exceeds the configured upload limit.")
                    output_file.write(chunk)
        finally:
            await upload.close()
        if not self._matches_signature(suffix, first_chunk):
            destination.unlink(missing_ok=True)
            raise APIProblem(400, "UNSUPPORTED_FILE_TYPE", f"{self._label(field_name)} content does not match its file type.")
        return destination

    def _matches_signature(self, suffix: str, content: bytes) -> bool:
        if suffix in self._SIGNATURES:
            return content.startswith(self._SIGNATURES[suffix])
        return content.startswith(b"\xff\xd8\xff")

    @staticmethod
    def _label(field_name: str) -> str:
        return {
            "question_paper": "Question paper",
            "model_answer": "Model answer",
            "student_answer_sheet": "Student answer sheet",
        }[field_name]
