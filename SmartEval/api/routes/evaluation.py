from __future__ import annotations

import logging
import time
from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import APIRouter, File, Form, Header, Query, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from api.errors import APIProblem
from api.file_storage import UploadStorage, UploadWorkspace
from api.schemas.requests import EvaluationMetadataRequest
from api.schemas.responses import EvaluationHistoryItemResponse, EvaluationListResponse, EvaluationResponse
from integration.evaluation_service import EvaluationRequest
from persistence.service import EvaluationPersistenceService, PersistedEvaluation, PersistenceError


router = APIRouter(prefix="/api/v1", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse, responses={
    400: {"description": "Invalid input"},
    413: {"description": "Uploaded file is too large"},
    422: {"description": "Evaluation input could not be processed"},
    502: {"description": "OCR processing failed"},
    503: {"description": "Evaluation history database unavailable"},
    500: {"description": "Internal server error"},
})
async def evaluate(
    request: Request,
    question_paper: UploadFile = File(..., description="Question paper PDF, PNG, JPG, or JPEG"),
    model_answer: UploadFile = File(..., description="Teacher model-answer PDF, PNG, JPG, or JPEG"),
    student_answer_sheet: UploadFile = File(..., description="Student handwritten PDF, PNG, JPG, or JPEG"),
    student_id: str | None = Form(default=None),
    student_name: str | None = Form(default=None),
    roll_number: str | None = Form(default=None),
    exam_id: str | None = Form(default=None),
    subject: str | None = Form(default=None),
    exam_name: str | None = Form(default=None),
    semester: str | None = Form(default=None),
    exam_date: str | None = Form(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> EvaluationResponse:
    settings = request.app.state.settings
    evaluation_id = _evaluation_id(idempotency_key)
    logger = logging.getLogger("smarteval")
    metadata = EvaluationMetadataRequest(
        student_id=student_id,
        student_name=student_name,
        roll_number=roll_number,
        exam_id=exam_id,
        subject=subject,
        exam_name=exam_name,
        semester=semester,
        exam_date=exam_date,
    )
    started = time.perf_counter()
    logger.info("API evaluation request received: %s", evaluation_id)
    try:
        with UploadWorkspace(settings.temp_directory, settings.keep_input_files, evaluation_id) as workspace:
            assert workspace.path is not None
            storage = UploadStorage(settings.max_upload_size_mb)
            question_path = await storage.save(question_paper, workspace.path, "question_paper")
            model_path = await storage.save(model_answer, workspace.path, "model_answer")
            student_path = await storage.save(student_answer_sheet, workspace.path, "student_answer_sheet")
            logger.info("API evaluation files validated: %s", evaluation_id)
            evaluation_request = EvaluationRequest(
                question_paper_path=question_path,
                model_answer_path=model_path,
                student_answer_sheet_path=student_path,
                student_id=metadata.student_id,
                student_name=metadata.student_name,
                roll_number=metadata.roll_number,
                exam_id=metadata.exam_id,
                subject=metadata.subject,
                exam_name=metadata.exam_name,
                semester=metadata.semester,
                exam_date=metadata.exam_date,
                report_id=evaluation_id,
            )
            service = request.app.state.evaluation_service_factory()
            execution = await run_in_threadpool(service.evaluate_and_export, evaluation_request)
    except APIProblem:
        raise
    except Exception as error:
        logger.exception("API evaluation request failed: %s", evaluation_id)
        raise APIProblem(500, "INTERNAL_ERROR", "The evaluation request could not be completed.", evaluation_id) from error

    report = replace(execution.report, report_id=evaluation_id)
    try:
        persistence = _persistence_service(request, evaluation_id)
        await run_in_threadpool(
            persistence.persist,
            report,
            question_paper_filename=question_paper.filename,
            model_answer_filename=model_answer.filename,
            student_answer_filename=student_answer_sheet.filename,
        )
    except APIProblem:
        raise
    except PersistenceError as error:
        logger.exception("Evaluation persistence failed: %s", evaluation_id)
        if settings.persistence_failure_is_error:
            raise APIProblem(503, "DATABASE_UNAVAILABLE", "The evaluation was completed but could not be saved.", evaluation_id) from error
        logger.warning("Evaluation completed without persistence: %s", evaluation_id)
    if report.status == "failed":
        problem = _failed_report_problem(report.warnings[0] if report.warnings else "Evaluation failed.", evaluation_id)
        logger.warning("API evaluation failed: %s code=%s", evaluation_id, problem.code)
        raise problem
    logger.info("API evaluation completed: %s status=%s duration=%.2fs", evaluation_id, report.status, time.perf_counter() - started)
    return _response_from_payload(evaluation_id, report.to_dict())


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(request: Request, evaluation_id: str) -> EvaluationResponse:
    try:
        persisted = await run_in_threadpool(_persistence_service(request, evaluation_id).get, evaluation_id)
    except APIProblem:
        raise
    except PersistenceError as error:
        raise APIProblem(503, "DATABASE_UNAVAILABLE", "Evaluation history is unavailable.", evaluation_id) from error
    if persisted is None:
        raise APIProblem(404, "EVALUATION_NOT_FOUND", "No evaluation exists for this identifier.", evaluation_id)
    return _response_from_payload(persisted.evaluation_id, persisted.report_payload)


@router.get("/evaluations", response_model=EvaluationListResponse)
async def list_evaluations(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    student_id: str | None = Query(default=None, max_length=128),
    exam_id: str | None = Query(default=None, max_length=128),
    status: str | None = Query(default=None, pattern="^(complete|partially_evaluated|failed)$"),
) -> EvaluationListResponse:
    try:
        result = await run_in_threadpool(
            _persistence_service(request).list,
            page=page,
            page_size=page_size,
            student_id=student_id,
            exam_id=exam_id,
            status=status,
        )
    except APIProblem:
        raise
    except PersistenceError as error:
        raise APIProblem(503, "DATABASE_UNAVAILABLE", "Evaluation history is unavailable.") from error
    return EvaluationListResponse(
        items=[_history_item(item) for item in result.items], total=result.total, page=result.page, page_size=result.page_size,
    )


@router.get("/students/{student_id}/evaluations", response_model=EvaluationListResponse)
async def student_evaluation_history(request: Request, student_id: str, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), exam_id: str | None = Query(default=None, max_length=128)) -> EvaluationListResponse:
    return await list_evaluations(request, page, page_size, student_id=student_id, exam_id=exam_id, status=None)


@router.get("/exams/{exam_id}/evaluations", response_model=EvaluationListResponse)
async def exam_evaluation_history(request: Request, exam_id: str, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100)) -> EvaluationListResponse:
    return await list_evaluations(request, page, page_size, student_id=None, exam_id=exam_id, status=None)


def _evaluation_id(idempotency_key: str | None) -> str:
    return f"evaluation_{uuid5(NAMESPACE_URL, idempotency_key).hex}" if idempotency_key else f"evaluation_{uuid4().hex}"


def _persistence_service(request: Request, evaluation_id: str | None = None) -> EvaluationPersistenceService:
    factory = getattr(request.app.state, "persistence_service_factory", None)
    if factory is None:
        raise APIProblem(503, "DATABASE_NOT_CONFIGURED", "Evaluation history is not configured.", evaluation_id)
    return factory()


def _response_from_payload(evaluation_id: str, payload: dict[str, object]) -> EvaluationResponse:
    report_data = dict(payload)
    report_data.pop("report_id", None)
    return EvaluationResponse.model_validate({"evaluation_id": evaluation_id, **report_data})


def _history_item(persisted: PersistedEvaluation) -> EvaluationHistoryItemResponse:
    payload = persisted.report_payload
    return EvaluationHistoryItemResponse.model_validate({
        "evaluation_id": persisted.evaluation_id,
        "status": persisted.status,
        "student_information": payload.get("student_information"),
        "exam_information": payload.get("exam_information"),
        "summary": payload.get("summary"),
        "created_at": persisted.created_at,
    })


def _failed_report_problem(message: str, evaluation_id: str) -> APIProblem:
    normalized = message.lower()
    if "no handwritten text" in normalized:
        return APIProblem(422, "OCR_EMPTY", "No handwritten text was extracted from the student answer sheet.", evaluation_id, "failed")
    if "handwritten text extraction failed" in normalized:
        return APIProblem(502, "OCR_FAILED", "Unable to extract handwritten text from the student answer sheet.", evaluation_id, "failed")
    if "no numbered student answers" in normalized:
        return APIProblem(422, "STUDENT_ANSWER_PARSE_FAILED", "Student answers could not be identified in the OCR text.", evaluation_id, "failed")
    if "duplicate question id" in normalized:
        return APIProblem(422, "QUESTION_PARSE_FAILED", "The question paper contains duplicate question identifiers.", evaluation_id, "failed")
    if "unsupported input format" in normalized or "was not found" in normalized:
        return APIProblem(400, "INVALID_INPUT", "One or more uploaded documents could not be processed.", evaluation_id, "error")
    if "question" in normalized and "parse" in normalized:
        return APIProblem(422, "QUESTION_PARSE_FAILED", "The question paper could not be parsed.", evaluation_id, "failed")
    if "model" in normalized and "parse" in normalized:
        return APIProblem(422, "MODEL_ANSWER_PARSE_FAILED", "The model answer could not be parsed.", evaluation_id, "failed")
    return APIProblem(500, "EVALUATION_FAILED", "The evaluation could not be completed.", evaluation_id, "failed")
