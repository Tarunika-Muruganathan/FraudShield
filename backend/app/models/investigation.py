from datetime import datetime, timezone
import json
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CaseInvestigation(Base):
    __tablename__ = "case_investigations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(
        String(36),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verification_id = Column(
        String(36),
        ForeignKey("case_verifications.id", ondelete="SET NULL"),
        nullable=True,
    )
    summary = Column(Text, nullable=False)
    key_observations = Column(Text, nullable=False, default="[]")  # JSON
    identified_discrepancies = Column(Text, nullable=False, default="[]")  # JSON
    missing_information = Column(Text, nullable=False, default="[]")  # JSON
    recommended_actions = Column(Text, nullable=False, default="[]")  # JSON
    supporting_evidence_ids = Column(Text, nullable=False, default="[]")  # JSON list
    confidence_explanation = Column(Text, nullable=False)
    human_review_status = Column(String(30), nullable=False, default="pending_review")
    provider_used = Column(String(50), nullable=False, default="mock")
    model_used = Column(String(100), nullable=False, default="deterministic-rule-engine")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    case = relationship("Case", back_populates="investigations")
    verification = relationship("CaseVerification")
    messages = relationship(
        "CaseInvestigationMessage",
        back_populates="investigation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseInvestigationMessage.created_at",
    )

    def get_key_observations(self) -> list:
        try:
            return json.loads(self.key_observations) if self.key_observations else []
        except Exception:
            return []

    def get_identified_discrepancies(self) -> list:
        try:
            return json.loads(self.identified_discrepancies) if self.identified_discrepancies else []
        except Exception:
            return []

    def get_missing_information(self) -> list:
        try:
            return json.loads(self.missing_information) if self.missing_information else []
        except Exception:
            return []

    def get_recommended_actions(self) -> list:
        try:
            return json.loads(self.recommended_actions) if self.recommended_actions else []
        except Exception:
            return []

    def get_supporting_evidence_ids(self) -> list:
        try:
            return json.loads(self.supporting_evidence_ids) if self.supporting_evidence_ids else []
        except Exception:
            return []


class CaseInvestigationMessage(Base):
    __tablename__ = "case_investigation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(
        String(36),
        ForeignKey("case_investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id = Column(
        String(36),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender = Column(String(20), nullable=False)  # 'investigator' or 'assistant'
    message = Column(Text, nullable=False)
    cited_evidence_ids = Column(Text, nullable=False, default="[]")  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    investigation = relationship("CaseInvestigation", back_populates="messages")

    def get_cited_evidence_ids(self) -> list:
        try:
            return json.loads(self.cited_evidence_ids) if self.cited_evidence_ids else []
        except Exception:
            return []

