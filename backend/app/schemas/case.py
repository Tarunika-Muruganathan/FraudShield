from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DisputeType = Literal["non_delivery", "fake_delivery", "payment_fraud", "amount_mismatch", "other"]
CaseStatus = Literal["pending", "investigating", "resolved", "rejected"]


class CaseCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    seller_name: str = Field(min_length=2, max_length=100)
    order_id: str = Field(min_length=2, max_length=100)
    transaction_id: str | None = Field(default=None, max_length=150)
    dispute_type: DisputeType
    description: str = Field(min_length=10, max_length=2000)


class CaseUpdate(BaseModel):
    customer_name: str | None = Field(default=None, min_length=2, max_length=100)
    seller_name: str | None = Field(default=None, min_length=2, max_length=100)
    transaction_id: str | None = Field(default=None, max_length=150)
    dispute_type: DisputeType | None = None
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    status: CaseStatus | None = None

    @model_validator(mode="after")
    def reject_null_for_required_fields(self):
        for field_name in ("customer_name", "seller_name", "dispute_type", "description"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    customer_name: str
    seller_name: str
    order_id: str
    transaction_id: str | None
    dispute_type: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
