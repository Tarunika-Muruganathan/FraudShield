from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceDocumentDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_id: str
    ocr_status: str
    ocr_error: str | None = None
    raw_text: str | None = None

    transaction_id: str | None = None
    order_id: str | None = None
    payment_amount: str | None = None
    currency: str | None = None
    payment_date: str | None = None
    payment_status: str | None = None
    sender_name: str | None = None
    receiver_name: str | None = None
    tracking_number: str | None = None
    delivery_date: str | None = None
    delivery_status: str | None = None

    processed_at: datetime | None = None

