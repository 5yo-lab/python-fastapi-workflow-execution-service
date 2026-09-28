import uuid

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_action_service, get_workflow_service
from app.schemas.action import ActionResponse
from app.schemas.workflow import (
    CreateWorkflowRequest,
    HistoryEntryResponse,
    TransitionRequest,
    WorkflowResponse,
    WorkflowSummaryResponse,
)
from app.services.action_service import ActionService
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _set_correlation_header(response: Response, correlation_id: uuid.UUID) -> None:
    response.headers["X-Correlation-Id"] = str(correlation_id)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: CreateWorkflowRequest,
    response: Response,
    service: WorkflowService = Depends(get_workflow_service),
):
    workflow = await service.create_workflow(body.reference, body.payload)
    _set_correlation_header(response, workflow.correlation_id)
    return workflow


@router.get("", response_model=list[WorkflowSummaryResponse])
async def list_workflows(
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_workflows()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    response: Response,
    service: WorkflowService = Depends(get_workflow_service),
):
    workflow = await service.get_workflow(workflow_id)
    _set_correlation_header(response, workflow.correlation_id)
    return workflow


@router.post("/{workflow_id}/transitions", response_model=WorkflowResponse)
async def apply_transition(
    workflow_id: uuid.UUID,
    body: TransitionRequest,
    response: Response,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    action_service: ActionService = Depends(get_action_service),
):
    workflow = await workflow_service.apply_manual_transition(
        workflow_id,
        body.action,
        body.expected_version,
        action_service=action_service,
    )
    _set_correlation_header(response, workflow.correlation_id)
    return workflow


@router.get("/{workflow_id}/history", response_model=list[HistoryEntryResponse])
async def get_history(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.get_history(workflow_id)


@router.get("/{workflow_id}/actions", response_model=list[ActionResponse])
async def get_workflow_actions(
    workflow_id: uuid.UUID,
    action_service: ActionService = Depends(get_action_service),
):
    return await action_service.list_for_workflow(workflow_id)