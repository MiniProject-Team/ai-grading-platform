from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    log_directory: Path
    output_directory: Path = Path("outputs")
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    correct_threshold: float = 0.80
    mostly_correct_threshold: float = 0.65
    partial_threshold: float = 0.40
    concept_threshold: float = 0.65
    relevance_threshold: float = 0.40
    completeness_threshold: float = 0.65
    semantic_weight: float = 0.40
    concept_weight: float = 0.30
    relevance_weight: float = 0.15
    completeness_weight: float = 0.15
    marks_decimal_places: int = 1
    feedback_excellent_threshold: float = 0.90
    feedback_good_threshold: float = 0.70
    feedback_partial_threshold: float = 0.40
    feedback_low_threshold: float = 0.10
    feedback_strength_threshold: float = 0.75
    feedback_weakness_threshold: float = 0.50
    continue_on_partial_ocr: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    max_upload_size_mb: int = 20
    temp_directory: Path = Path("temp")
    keep_input_files: bool = False
    cors_allowed_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:5173")
    database_url: str | None = None
    database_echo: bool = False
    persistence_failure_is_error: bool = True
    retain_evaluation_content: bool = True
    smarthr_provider: str = "local"
    debug: bool = False

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        root = Path(__file__).resolve().parent.parent
        return cls(
            log_directory=root / os.getenv("LOG_DIRECTORY", "logs"),
            output_directory=root / os.getenv("OUTPUT_DIRECTORY", "outputs"),
            semantic_model_name=os.getenv("SEMANTIC_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
            correct_threshold=float(os.getenv("SEMANTIC_CORRECT_THRESHOLD", "0.80")),
            mostly_correct_threshold=float(os.getenv("MOSTLY_CORRECT_THRESHOLD", "0.65")),
            partial_threshold=float(os.getenv("PARTIAL_THRESHOLD", "0.40")),
            concept_threshold=float(os.getenv("CONCEPT_THRESHOLD", "0.65")),
            relevance_threshold=float(os.getenv("RELEVANCE_THRESHOLD", "0.40")),
            completeness_threshold=float(os.getenv("COMPLETENESS_THRESHOLD", "0.65")),
            semantic_weight=float(os.getenv("SEMANTIC_WEIGHT", "0.40")),
            concept_weight=float(os.getenv("CONCEPT_WEIGHT", "0.30")),
            relevance_weight=float(os.getenv("RELEVANCE_WEIGHT", "0.15")),
            completeness_weight=float(os.getenv("COMPLETENESS_WEIGHT", "0.15")),
            marks_decimal_places=int(os.getenv("MARKS_DECIMAL_PLACES", "1")),
            feedback_excellent_threshold=float(os.getenv("FEEDBACK_EXCELLENT_THRESHOLD", "0.90")),
            feedback_good_threshold=float(os.getenv("FEEDBACK_GOOD_THRESHOLD", "0.70")),
            feedback_partial_threshold=float(os.getenv("FEEDBACK_PARTIAL_THRESHOLD", "0.40")),
            feedback_low_threshold=float(os.getenv("FEEDBACK_LOW_THRESHOLD", "0.10")),
            feedback_strength_threshold=float(os.getenv("FEEDBACK_STRENGTH_THRESHOLD", "0.75")),
            feedback_weakness_threshold=float(os.getenv("FEEDBACK_WEAKNESS_THRESHOLD", "0.50")),
            continue_on_partial_ocr=os.getenv("CONTINUE_ON_PARTIAL_OCR", "true").lower() == "true",
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "8000")),
            max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "20")),
            temp_directory=root / os.getenv("TEMP_DIRECTORY", "temp"),
            keep_input_files=os.getenv("KEEP_INPUT_FILES", "false").lower() == "true",
            cors_allowed_origins=tuple(origin.strip() for origin in os.getenv(
                "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173",
            ).split(",") if origin.strip()),
            database_url=os.getenv("DATABASE_URL") or None,
            database_echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            persistence_failure_is_error=os.getenv("PERSISTENCE_FAILURE_IS_ERROR", "true").lower() == "true",
            retain_evaluation_content=os.getenv("RETAIN_EVALUATION_CONTENT", "true").lower() == "true",
            smarthr_provider=os.getenv("SMARTHR_PROVIDER", "local").lower(),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    @property
    def reports_directory(self) -> Path:
        return self.output_directory / "reports"
