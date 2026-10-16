"""
Tasks and Approvals routes.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser, ManagerOrAbove
from ..dependencies import ApprovalRepoDep, AuditRepoDep, NotifRepoDep, TaskRepoDep
from ..models import (
    AuditAction,
    AuditRecord,
    Approval,
    ApprovalStatus,
    Notification,
    NotificationType,
    Task,
    UserProfile,
    utcnow,
)
from ..schemas import (
    ApprovalCreate,
    ApprovalOut,
    ApprovalResolve,
    PaginatedResponse,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

router = APIRouter(tags=["tasks"])


# ─── Tasks ────────────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=PaginatedResponse[TaskOut], summary="List tasks")
async def list_tasks(
    current_user: CurrentUser,
    task_repo: TaskRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    assignee_id: str | None = None,
    project_id: str | None = None,
    mine: bool = False,
) -> PaginatedResponse[TaskOut]:
    if mine:
        assignee_id = current_user.id
    skip = (page - 1) * page_size
    tasks, total = await task_repo.list(
        skip=skip, limit=page_size,
        assignee_id=assignee_id, project_id=project_id,
    )
    return PaginatedResponse(
        items=[TaskOut.model_validate(t.model_dump()) for t in tasks],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED,
             summary="Create task")
async def create_task(
    body: TaskCreate,
    current_user: CurrentUser,
    task_repo: TaskRepoDep,
    audit_repo: AuditRepoDep,
    notif_repo: NotifRepoDep,
) -> TaskOut:
    task = Task(
        **body.model_dump(),
        reporter_id=current_user.id,
    )
    created = await task_repo.create(task)

    if created.assignee_id and created.assignee_id != current_user.id:
        await notif_repo.create(Notification(
            user_id=created.assignee_id,
            type=NotificationType.TASK_ASSIGNED,
            title="New task assigned",
            body=f"{current_user.name} assigned you: '{created.title}'",
            link="/app/tasks",
        ))

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="task",
        resource_id=created.id,
        description=f"Created task: {created.title}",
    ))
    return TaskOut.model_validate(created.model_dump())


@router.get("/tasks/{task_id}", response_model=TaskOut, summary="Get task")
async def get_task(
    task_id: str,
    current_user: CurrentUser,
    task_repo: TaskRepoDep,
) -> TaskOut:
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskOut.model_validate(task.model_dump())


@router.patch("/tasks/{task_id}", response_model=TaskOut, summary="Update task")
async def update_task(
    task_id: str,
    body: TaskUpdate,
    current_user: CurrentUser,
    task_repo: TaskRepoDep,
    audit_repo: AuditRepoDep,
) -> TaskOut:
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    task.updated_at = utcnow()
    updated = await task_repo.update(task)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="task",
        resource_id=task_id,
        description=f"Updated task: {updated.title}",
    ))
    return TaskOut.model_validate(updated.model_dump())


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete task")
async def delete_task(
    task_id: str,
    current_user: CurrentUser,
    task_repo: TaskRepoDep,
    audit_repo: AuditRepoDep,
) -> Response:
    if not await task_repo.delete(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.DELETE,
        resource_type="task",
        resource_id=task_id,
    ))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Approvals ────────────────────────────────────────────────────────────────

@router.get("/approvals", response_model=PaginatedResponse[ApprovalOut], summary="List approvals")
@router.get("/tasks/approvals", response_model=PaginatedResponse[ApprovalOut], summary="List approvals alias")
async def list_approvals(
    current_user: CurrentUser,
    approval_repo: ApprovalRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mine: bool = False,
) -> PaginatedResponse[ApprovalOut]:
    skip = (page - 1) * page_size
    approvals, total = await approval_repo.list(
        skip=skip, limit=page_size,
        user_id=current_user.id if mine else None,
    )
    return PaginatedResponse(
        items=[ApprovalOut.model_validate(a.model_dump()) for a in approvals],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/approvals", response_model=ApprovalOut, status_code=status.HTTP_201_CREATED,
             summary="Submit approval request")
async def create_approval(
    body: ApprovalCreate,
    current_user: CurrentUser,
    approval_repo: ApprovalRepoDep,
    notif_repo: NotifRepoDep,
    audit_repo: AuditRepoDep,
) -> ApprovalOut:
    approval = Approval(
        **body.model_dump(),
        requester_id=current_user.id,
    )
    created = await approval_repo.create(approval)

    await notif_repo.create(Notification(
        user_id=created.approver_id,
        type=NotificationType.APPROVAL_REQUESTED,
        title="Approval request",
        body=f"{current_user.name} has submitted: '{created.title}'",
        link="/app/tasks",
    ))
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="approval",
        resource_id=created.id,
        description=f"Submitted approval: {created.title}",
    ))
    return ApprovalOut.model_validate(created.model_dump())


@router.post("/approvals/{approval_id}/resolve", response_model=ApprovalOut,
             summary="Approve or reject a request (approver only)")
@router.post("/tasks/approvals/{approval_id}/resolve", response_model=ApprovalOut,
             summary="Approve or reject a request alias")
async def resolve_approval(
    approval_id: str,
    body: ApprovalResolve,
    current_user: CurrentUser,
    approval_repo: ApprovalRepoDep,
    notif_repo: NotifRepoDep,
    audit_repo: AuditRepoDep,
) -> ApprovalOut:
    approval = await approval_repo.get(approval_id)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the designated approver may resolve this request")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Approval has already been resolved")

    approval.status = body.status
    approval.decision_note = body.decision_note
    approval.resolved_at = utcnow()
    updated = await approval_repo.update(approval)

    await notif_repo.create(Notification(
        user_id=updated.requester_id,
        type=NotificationType.APPROVAL_RESOLVED,
        title=f"Approval {updated.status.value}",
        body=f"'{updated.title}' was {updated.status.value} by {current_user.name}.",
        link="/app/tasks",
    ))
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="approval",
        resource_id=approval_id,
        description=f"Resolved approval as {updated.status.value}: {updated.title}",
    ))
    return ApprovalOut.model_validate(updated.model_dump())
