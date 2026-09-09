from .evaluation import router as evaluation_router
from .question_paper import question_paper_router
from .health import router as health_router

__all__ = ["evaluation_router", "health_router", "question_paper_router"]
