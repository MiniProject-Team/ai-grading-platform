from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.errors import APIProblem
from api.routes import evaluation_router, health_router
from api.schemas.responses import ErrorDetailResponse, ErrorResponse
from config.settings import Settings
from integration.evaluation_service import EvaluationService
from integration.smarthtr_client import create_smarthtr_client
from integration.student_text_provider import SharedRuntimeSmartHTRStudentTextProvider, SmartHTRIntegrationService
from persistence.database import create_database_engine, create_session_factory
from persistence.service import EvaluationPersistenceService
from utils.logger import configure_logging


def create_app(
    settings: Settings | None = None,
    evaluation_service_factory: Callable[[], EvaluationService] | None = None,
    persistence_service_factory: Callable[[], EvaluationPersistenceService] | None = None,
) -> FastAPI:
    settings = settings or Settings.from_environment()
    configure_logging(settings)
    app = FastAPI(title="SmartEval API", version="1.0.0")
    app.state.settings = settings
    app.state.evaluation_service_factory = evaluation_service_factory or _default_service_factory(settings)
    default_persistence = _default_persistence_service_factory(settings)
    app.state.persistence_service_factory = persistence_service_factory or default_persistence[0]
    app.state.database_engine = default_persistence[1]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.include_router(health_router)
    app.include_router(evaluation_router)
    _register_exception_handlers(app)
    return app


def _default_service_factory(settings: Settings) -> Callable[[], EvaluationService]:
    shared_client = create_smarthtr_client(settings)

    def create_service() -> EvaluationService:
        # Keep one SmartHTR model runtime for the application, but give each
        # request its own provider state and last-result metadata.
        provider = SharedRuntimeSmartHTRStudentTextProvider(
            SmartHTRIntegrationService(shared_client),
            continue_on_partial=settings.continue_on_partial_ocr,
        )
        return EvaluationService(settings, student_text_provider=provider)

    return create_service


def _default_persistence_service_factory(
    settings: Settings,
) -> tuple[Callable[[], EvaluationPersistenceService] | None, object | None]:
    if not settings.database_url:
        return None, None
    engine = create_database_engine(settings.database_url, echo=settings.database_echo)
    session_factory = create_session_factory(engine)
    return lambda: EvaluationPersistenceService(session_factory, settings), engine


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIProblem)
    async def handle_api_problem(request: Request, error: APIProblem) -> JSONResponse:
        payload = ErrorResponse(
            status=error.response_status,
            evaluation_id=error.evaluation_id,
            error=ErrorDetailResponse(code=error.code, message=error.message),
        )
        return JSONResponse(status_code=error.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        payload = ErrorResponse(
            status="error",
            error=ErrorDetailResponse(code="INVALID_INPUT", message="Required upload fields are missing or invalid."),
        )
        return JSONResponse(status_code=400, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logging.getLogger("smarteval").exception("Unhandled API error")
        payload = ErrorResponse(
            status="error",
            error=ErrorDetailResponse(code="INTERNAL_ERROR", message="The request could not be completed."),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())


app = create_app()
