import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="evidence")
    document_data = relationship(
        "EvidenceDocumentData",
        back_populates="evidence",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
