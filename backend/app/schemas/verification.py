from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SeverityLevel = Literal["CRITICAL", "WARNING", "INFO"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class DiscrepancyItem(BaseModel):
    code: str
    severity: SeverityLevel
    domain: str  # PAYMENT, ORDER, DELIVERY, TIMELINE, IDENTITY
    title: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class MatchItem(BaseModel):
    domain: str
    title: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class MissingEvidenceItem(BaseModel):
    code: str
    severity: SeverityLevel = "WARNING"
    title: str
    description: str


class CaseVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    risk_score: int
    risk_level: RiskLevel
    summary: str
    discrepancies: list[DiscrepancyItem] = Field(default_factory=list)
    matches: list[MatchItem] = Field(default_factory=list)
    missing_evidence: list[MissingEvidenceItem] = Field(default_factory=list)
    verified_at: datetime

