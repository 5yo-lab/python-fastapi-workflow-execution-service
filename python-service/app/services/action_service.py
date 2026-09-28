import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.errors import AppError, ErrorCode, NotFoundError
from app.domain.state_machine import Action, ActionType
from app.models.workflow import Workflow
from app.models.workflow_action import ActionStatus, WorkflowAction


class ActionService:
    def __init__(self, db: AsyncSession, workflow_service):
        self.db = db
        self.workflow_service = workflow_service

    async def enqueue(self, workflow: Workflow, action_type: ActionType) -> WorkflowAction:
        action = WorkflowAction(
            workflow_id=workflow.id,
            type=action_type.value,
            payload=workflow.payload,
        )
        self.db.add(action)
        await self.db.flush()
        return action

    async def get_pending(self) -> list[WorkflowAction]:
        result = await self.db.execute(
            select(WorkflowAction)
            .where(
                WorkflowAction.status == ActionStatus.PENDING.value,
                WorkflowAction.attempt < WorkflowAction.max_attempts,
            )
            .order_by(WorkflowAction.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_workflow(self, workflow_id: uuid.UUID) -> list[WorkflowAction]:
        await self.workflow_service.get_workflow(workflow_id)
        result = await self.db.execute(
            select(WorkflowAction)
            .where(WorkflowAction.workflow_id == workflow_id)
            .order_by(WorkflowAction.created_at.asc())
        )
        return list(result.scalars().all())

    async def claim_action(self, action_id: uuid.UUID) -> WorkflowAction:
        action = await self._get_action_with_workflow(action_id)

        if action.status == ActionStatus.IN_PROGRESS.value:
            return action

        if action.status != ActionStatus.PENDING.value:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Action {action_id} cannot be claimed from status {action.status}",
                status_code=409,
            )

        action.status = ActionStatus.IN_PROGRESS.value
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def submit_result(
        self,
        action_id: uuid.UUID,
        success: bool,
        result: dict | None = None,
        error: str | None = None,
    ) -> WorkflowAction:
        action = await self._get_action_with_workflow(action_id)

        if action.status in (ActionStatus.SUCCESS.value, ActionStatus.FAILED.value):
            return action

        if action.status != ActionStatus.IN_PROGRESS.value:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Action {action_id} must be IN_PROGRESS before submitting a result",
                status_code=400,
            )

        action.completed_at = datetime.now(timezone.utc)

        if success:
            action.status = ActionStatus.SUCCESS.value
            action.result = result
            automated_action = (
                Action.APPROVE if action.type == ActionType.VALIDATE.value else Action.COMPLETE
            )
            await self.workflow_service.apply_automated_transition(
                action.workflow, automated_action
            )
        else:
            action.error = error
            if action.attempt < action.max_attempts:
                action.status = ActionStatus.PENDING.value
                action.attempt += 1
                action.completed_at = None
            else:
                action.status = ActionStatus.FAILED.value
                automated_action = (
                    Action.REJECT if action.type == ActionType.VALIDATE.value else Action.FAIL
                )
                await self.workflow_service.apply_automated_transition(
                    action.workflow, automated_action
                )

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def _get_action_with_workflow(self, action_id: uuid.UUID) -> WorkflowAction:
        result = await self.db.execute(
            select(WorkflowAction)
            .options(selectinload(WorkflowAction.workflow))
            .where(WorkflowAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise NotFoundError(f"Action {action_id} not found")
        return action