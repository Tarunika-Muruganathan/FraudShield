from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ObservationItem(BaseModel):
    title: str
    observation: str
    domain: str  # PAYMENT, ORDER, DELIVERY, TIMELINE, IDENTITY
    evidence_ids: list[str] = Field(default_factory=list)
    is_supported: bool = True
    support_note: str | None = None


class DiscrepancyExplanation(BaseModel):
    code: str
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    title: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    action: str
    rationale: str


class CaseInvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    verification_id: str | None = None
    summary: str
    key_observations: list[ObservationItem] = Field(default_factory=list)
    identified_discrepancies: list[DiscrepancyExplanation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    related_verification_codes: list[str] = Field(default_factory=list)
    confidence_explanation: str
    human_review_status: str
    provider_used: str
    model_used: str
    created_at: datetime


class InvestigationChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class InvestigationChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    case_id: str
    sender: Literal["investigator", "assistant"]
    message: str
    cited_evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime

