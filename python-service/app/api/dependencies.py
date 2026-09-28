from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.action_service import ActionService
from app.services.workflow_service import WorkflowService


async def get_workflow_service(
    db: AsyncSession = Depends(get_db),
) -> WorkflowService:
    return WorkflowService(db)


async def get_action_service(
    db: AsyncSession = Depends(get_db),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> ActionService:
    return ActionService(db, workflow_service)