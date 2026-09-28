import uuid

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_action_service
from app.schemas.action import (
    ActionResponse,
    ActionResultRequest,
    PendingActionResponse,
)
from app.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/pending", response_model=list[PendingActionResponse])
async def get_pending_actions(
    service: ActionService = Depends(get_action_service),
):
    return await service.get_pending()


@router.post("/{action_id}/claim", response_model=ActionResponse)
async def claim_action(
    action_id: uuid.UUID,
    service: ActionService = Depends(get_action_service),
):
    return await service.claim_action(action_id)


@router.post("/{action_id}/result", response_model=ActionResponse)
async def submit_action_result(
    action_id: uuid.UUID,
    body: ActionResultRequest,
    service: ActionService = Depends(get_action_service),
):
    return await service.submit_result(
        action_id,
        success=body.success,
        result=body.result,
        error=body.error,
    )