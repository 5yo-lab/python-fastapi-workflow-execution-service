import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.state_machine import Action


class CreateWorkflowRequest(BaseModel):
    reference: str
    payload: dict
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reference": "WF-001",
                "payload": {"customerId": "customer-1", "amount": 100},
            }
        }
    )

class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    payload: dict
    state: str
    version: int
    correlation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime = Field(serialization_alias="updatedAt")


class WorkflowSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    state: str
    version: int
    updated_at: datetime = Field(serialization_alias="updatedAt")


class TransitionRequest(BaseModel):
    action: Action
    expected_version: int | None = Field(default=None, alias="expectedVersion")

    model_config = ConfigDict(populate_by_name=True)


class HistoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    from_state: str = Field(serialization_alias="fromState")
    to_state: str = Field(serialization_alias="toState")
    action: str
    correlation_id: uuid.UUID = Field(serialization_alias="correlationId")
    timestamp: datetime