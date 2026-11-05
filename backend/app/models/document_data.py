import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class EvidenceDocumentData(Base):
    __tablename__ = "evidence_document_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(
        String(36),
        ForeignKey("evidence.evidence_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    ocr_status = Column(String(30), nullable=False, default="pending")  # pending, completed, unreadable, failed
    ocr_error = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)

    # Structured Extracted Fields
    transaction_id = Column(String(150), nullable=True)
    order_id = Column(String(100), nullable=True)
    payment_amount = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    payment_date = Column(String(50), nullable=True)
    payment_status = Column(String(50), nullable=True)
    sender_name = Column(String(150), nullable=True)
    receiver_name = Column(String(150), nullable=True)
    tracking_number = Column(String(150), nullable=True)
    delivery_date = Column(String(50), nullable=True)
    delivery_status = Column(String(50), nullable=True)

    processed_at = Column(DateTime(timezone=True), nullable=True)

    evidence = relationship("Evidence", back_populates="document_data")

