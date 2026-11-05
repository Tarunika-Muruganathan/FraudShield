from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models.case import Case  # noqa: F401 - register model metadata
from app.models.document_data import EvidenceDocumentData  # noqa: F401 - register model metadata
from app.models.evidence import Evidence  # noqa: F401 - register model metadata
from app.models.verification import CaseVerification  # noqa: F401 - register model metadata
from app.routes.cases import router as cases_router
from app.routes.evidence import router as evidence_router
from app.routes.ocr import router as ocr_router
from app.routes.verification import router as verification_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Payment-to-Delivery Fraud Investigation API",
    description="Case-management API for evidence-based payment and delivery disputes.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(ocr_router)
app.include_router(verification_router)


@app.get("/")
def home():
    return {"message": "Payment Fraud Investigation API is running", "status": "online"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
