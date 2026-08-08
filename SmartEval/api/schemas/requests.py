from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvaluationMetadataRequest(BaseModel):
    """Optional form metadata; uploaded files remain FastAPI parameters."""

    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str | None = Field(default=None, max_length=128)
    student_name: str | None = Field(default=None, max_length=256)
    roll_number: str | None = Field(default=None, max_length=128)
    exam_id: str | None = Field(default=None, max_length=128)
    subject: str | None = Field(default=None, max_length=256)
    exam_name: str | None = Field(default=None, max_length=256)
    semester: str | None = Field(default=None, max_length=128)
    exam_date: str | None = Field(default=None, max_length=64)
