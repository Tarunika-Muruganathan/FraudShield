import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String(100), nullable=False)
    seller_name = Column(String(100), nullable=False)
    order_id = Column(String(100), nullable=False, index=True)
    transaction_id = Column(String(150), nullable=True, index=True)
    dispute_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    evidence = relationship(
        "Evidence",
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    verifications = relationship(
        "CaseVerification",
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(CaseVerification.verified_at)",
    )
    investigations = relationship(
        "CaseInvestigation",
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(CaseInvestigation.created_at)",
    )
