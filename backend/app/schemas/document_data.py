from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaymentIntelligence(BaseModel):
    transaction_id: str | None = None
    payment_amount: str | None = None
    currency: str | None = None
    payment_date: str | None = None
    payment_status: str | None = None
    sender_name: str | None = None
    receiver_name: str | None = None
    payment_reference: str | None = None


class OrderIntelligence(BaseModel):
    order_id: str | None = None
    order_date: str | None = None
    product_description: str | None = None
    order_amount: str | None = None
    customer_information: str | None = None


class DeliveryIntelligence(BaseModel):
    tracking_number: str | None = None
    delivery_date: str | None = None
    delivery_status: str | None = None
    recipient_information: str | None = None
    delivery_address: str | None = None


class ExtractedDataResponse(BaseModel):
    evidence_id: str
    ocr_status: str
    payment: PaymentIntelligence
    order: OrderIntelligence
    delivery: DeliveryIntelligence
    processed_at: datetime | None = None


class EvidenceDocumentDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_id: str
    ocr_status: str
    ocr_error: str | None = None
    raw_text: str | None = None

    # Payment fields
    transaction_id: str | None = None
    payment_amount: str | None = None
    currency: str | None = None
    payment_date: str | None = None
    payment_status: str | None = None
    sender_name: str | None = None
    receiver_name: str | None = None
    payment_reference: str | None = None

    # Order fields
    order_id: str | None = None
    order_date: str | None = None
    product_description: str | None = None
    order_amount: str | None = None
    customer_information: str | None = None

    # Delivery fields
    tracking_number: str | None = None
    delivery_date: str | None = None
    delivery_status: str | None = None
    recipient_information: str | None = None
    delivery_address: str | None = None

    processed_at: datetime | None = None

