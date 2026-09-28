import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PendingActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    workflow_id: uuid.UUID = Field(serialization_alias="workflowId")
    type: str
    status: str
    attempt: int
    max_attempts: int = Field(serialization_alias="maxAttempts")
    payload: dict
    created_at: datetime = Field(serialization_alias="createdAt")


class ActionResultRequest(BaseModel):
    success: bool
    result: dict | None = None
    error: str | None = None


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    workflow_id: uuid.UUID = Field(serialization_alias="workflowId")
    type: str
    status: str
    attempt: int
    max_attempts: int = Field(serialization_alias="maxAttempts")
    payload: dict
    result: dict | None = None
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")