from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    case_id: str
    event_type: str
    category: str
    title: str
    description: str
    event_timestamp: datetime | None = None
    recorded_at: datetime
    actor: str | None = None
    related_evidence_ids: list[str] = Field(default_factory=list)
    related_verification_id: str | None = None
    related_investigation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

