from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from api.errors import APIProblem
from question_paper.service import QuestionPaperService


question_paper_router = APIRouter(prefix="/api/v1/question-papers", tags=["question papers"])
_SUFFIXES = {".pdf", ".txt", ".json"}


@question_paper_router.post("/analyze")
async def analyze_question_paper(
    question_paper: UploadFile = File(..., description="Text-based PDF or extracted text question paper"),
    generate_answers: bool = Form(False),
    answer_depth: str = Form("exam_ready"),
) -> dict:
    suffix = Path(question_paper.filename or "").suffix.lower()
    if suffix not in _SUFFIXES:
        raise APIProblem(400, "UNSUPPORTED_INPUT", "Upload a PDF, TXT, or JSON question paper.")
    with TemporaryDirectory(prefix="question-paper-") as directory:
        path = Path(directory) / f"paper{suffix}"
        content = await question_paper.read()
        path.write_bytes(content)
        service = QuestionPaperService()
        try:
            if generate_answers:
                paper, answer_sheet = await run_in_threadpool(service.model_answer_sheet, path, answer_depth)
                return {"paper": paper, "model_answer_sheet": answer_sheet}
            paper = await run_in_threadpool(service.analyze, path)
            return {"paper": paper.to_dict()}
        except ValueError as error:
            raise APIProblem(422, "QUESTION_PAPER_PARSE_FAILED", str(error)) from error
