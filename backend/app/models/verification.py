from datetime import datetime, timezone
import json
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CaseVerification(Base):
    __tablename__ = "case_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(
        String(36),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_score = Column(Integer, nullable=False)  # 0 - 100
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    summary = Column(Text, nullable=False)
    discrepancies = Column(Text, nullable=False, default="[]")  # JSON string
    matches = Column(Text, nullable=False, default="[]")  # JSON string
    missing_evidence = Column(Text, nullable=False, default="[]")  # JSON string
    verified_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    case = relationship("Case", back_populates="verifications")

    def get_discrepancies_list(self) -> list:
        try:
            return json.loads(self.discrepancies) if self.discrepancies else []
        except Exception:
            return []

    def get_matches_list(self) -> list:
        try:
            return json.loads(self.matches) if self.matches else []
        except Exception:
            return []

    def get_missing_evidence_list(self) -> list:
        try:
            return json.loads(self.missing_evidence) if self.missing_evidence else []
        except Exception:
            return []

