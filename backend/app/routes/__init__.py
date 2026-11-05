from app.routes.cases import router as cases_router
from app.routes.evidence import router as evidence_router
from app.routes.investigations import router as investigations_router
from app.routes.ocr import router as ocr_router
from app.routes.timeline import router as timeline_router
from app.routes.verification import router as verification_router

__all__ = [
    "cases_router",
    "evidence_router",
    "ocr_router",
    "verification_router",
    "investigations_router",
    "timeline_router",
]
