from datetime import datetime, timezone
import json
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(
        String(36),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key = Column(String(150), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    category = Column(String(30), nullable=False, index=True)  # case, evidence, ocr, verification, investigation, human_review
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    actor = Column(String(50), nullable=True)  # investigator, system, ocr_engine, verification_engine, ai_agent
    related_evidence_ids = Column(Text, nullable=False, default="[]")  # JSON array
    related_verification_id = Column(String(36), nullable=True)
    related_investigation_id = Column(String(36), nullable=True)
    metadata_json = Column("metadata", Text, nullable=False, default="{}")  # JSON dict

    case = relationship("Case", back_populates="timeline_events")

    def get_related_evidence_ids(self) -> list:
        try:
            return json.loads(self.related_evidence_ids) if self.related_evidence_ids else []
        except Exception:
            return []

    def get_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

