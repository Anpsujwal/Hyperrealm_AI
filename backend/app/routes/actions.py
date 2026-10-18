"""
Action execution and reporting routes.
Exposes consequential action execution and reporting history.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..auth import CurrentUser
from ..dependencies import ActionExecutionRepoDep
from ..models import ActionExecutionRecord, UserRole
from ..schemas import (
    ActionExecutionRequest,
    ActionExecutionResponse,
    PaginatedResponse,
)
from ..services.workflow import WorkflowService

router = APIRouter(prefix="/actions", tags=["actions"])

_workflow: WorkflowService | None = None


def get_workflow() -> WorkflowService:
    global _workflow
    if _workflow is None:
        _workflow = WorkflowService()
    return _workflow


@router.get("", response_model=PaginatedResponse[ActionExecutionResponse],
            summary="List action executions")
async def list_actions(
    current_user: CurrentUser,
    act_repo: ActionExecutionRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ActionExecutionResponse]:
    skip = (page - 1) * page_size
    user_filter = None if current_user.role == UserRole.ADMIN else current_user.id
    records, total = await act_repo.list(skip=skip, limit=page_size, user_id=user_filter)
    return PaginatedResponse(
        items=[ActionExecutionResponse.model_validate(r.model_dump()) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/execute", response_model=ActionExecutionResponse,
             status_code=status.HTTP_200_OK, summary="Execute an approved or authorized action")
async def execute_action_endpoint(
    body: ActionExecutionRequest,
    current_user: CurrentUser,
) -> ActionExecutionResponse:
    workflow = get_workflow()
    record = await workflow.execute_action(
        action_type=body.action_type,
        parameters=body.parameters,
        executor=current_user,
        approval_id=body.approval_id,
        idempotency_key=body.idempotency_key,
    )
    return ActionExecutionResponse.model_validate(record.model_dump())
