from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.document_data import EvidenceDocumentDataResponse


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    case_id: str
    filename: str
    stored_filename: str
    content_type: str | None
    file_size: int
    sha256_hash: str
    extracted_text: str | None
    uploaded_at: datetime
    document_data: EvidenceDocumentDataResponse | None = None

