import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import InvalidTransitionError, NotFoundError, StaleVersionError
from app.domain.state_machine import (
    Action,
    AUTOMATED_ACTIONS,
    MANUAL_ACTIONS,
    State,
    action_type_for_transition,
    get_next_state,
    is_terminal,
)
from app.models.workflow import Workflow
from app.models.workflow_history import WorkflowHistory


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(self, reference: str, payload: dict) -> Workflow:
        workflow = Workflow(reference=reference, payload=payload)
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: uuid.UUID) -> Workflow:
        workflow = await self.db.get(Workflow, workflow_id)
        if workflow is None:
            raise NotFoundError(f"Workflow {workflow_id} not found")
        return workflow

    async def list_workflows(self) -> list[Workflow]:
        result = await self.db.execute(
            select(Workflow).order_by(Workflow.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_history(self, workflow_id: uuid.UUID) -> list[WorkflowHistory]:
        await self.get_workflow(workflow_id)
        result = await self.db.execute(
            select(WorkflowHistory)
            .where(WorkflowHistory.workflow_id == workflow_id)
            .order_by(WorkflowHistory.timestamp.asc())
        )
        return list(result.scalars().all())

    async def apply_manual_transition(
        self,
        workflow_id: uuid.UUID,
        action: Action,
        expected_version: int | None = None,
        action_service=None,
    ) -> Workflow:
        workflow = await self.get_workflow(workflow_id)

        if expected_version is not None and workflow.version != expected_version:
            raise StaleVersionError(
                f"Expected version {expected_version}, but workflow is at {workflow.version}"
            )

        if action not in MANUAL_ACTIONS:
            raise InvalidTransitionError(f"Action {action} is not allowed via API")

        workflow = await self._apply_transition(workflow, action)

        action_type = action_type_for_transition(action)
        if action_type is not None and action_service is not None:
            await action_service.enqueue(workflow, action_type)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def apply_automated_transition(
        self, workflow: Workflow, action: Action
    ) -> Workflow:
        if action not in AUTOMATED_ACTIONS:
            raise InvalidTransitionError(
                f"Action {action} is not an automated transition"
            )
        workflow = await self._apply_transition(workflow, action)
        await self.db.flush()
        return workflow

    async def _apply_transition(self, workflow: Workflow, action: Action) -> Workflow:
        current = State(workflow.state)

        if is_terminal(current):
            raise InvalidTransitionError(
                f"Workflow is already in terminal state {current}"
            )

        next_state = get_next_state(current, action)
        from_state = workflow.state

        workflow.state = next_state.value
        workflow.version += 1

        self.db.add(
            WorkflowHistory(
                workflow_id=workflow.id,
                from_state=from_state,
                to_state=next_state.value,
                action=action.value,
                correlation_id=workflow.correlation_id,
            )
        )
        return workflow