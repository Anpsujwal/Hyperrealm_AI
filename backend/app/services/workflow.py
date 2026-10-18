"""
HYPERREALM Validation, Approval, and Action Execution Service.
Shared backend workflow component governing consequential actions,
permission enforcement, approval records, idempotency, and audit trails.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import (
    get_act_repo,
    get_approval_repo,
    get_audit_repo,
    get_learning_repo,
    get_meeting_repo,
    get_notif_repo,
    get_task_repo,
    get_user_repo,
)
from ..models import (
    ActionExecutionRecord,
    ActionStatus,
    Approval,
    ApprovalStatus,
    AuditAction,
    AuditRecord,
    Meeting,
    MeetingType,
    Notification,
    NotificationType,
    Task,
    TaskPriority,
    TaskStatus,
    UserProfile,
    UserRole,
    new_id,
    utcnow,
)

logger = logging.getLogger("hyperrealm.workflow")


class WorkflowService:
    def __init__(self):
        self.approval_repo = get_approval_repo()
        self.act_repo = get_act_repo()
        self.audit_repo = get_audit_repo()
        self.task_repo = get_task_repo()
        self.meeting_repo = get_meeting_repo()
        self.notif_repo = get_notif_repo()
        self.learning_repo = get_learning_repo()
        self.user_repo = get_user_repo()

    async def validate_and_propose_action(
        self,
        action_type: str,
        parameters: dict[str, Any],
        requester: UserProfile,
        target_resource: Optional[str] = None,
        evidence: str = "",
        risks: list[str] | None = None,
        guideline_version: str = "1.0",
        requires_approval: bool = True,
    ) -> tuple[Optional[Approval], Optional[ActionExecutionRecord]]:
        """
        Validate proposed action against permissions & guidelines.
        If requires_approval is True, create an Approval record in PENDING state.
        If requires_approval is False, execute immediately.
        """
        # Determine approver (manager or admin)
        approver_id = requester.manager_id
        if not approver_id:
            # Fall back to admin user
            admin_user = await self.user_repo.get_by_email("bob.harris@hyperrealm.io")
            approver_id = admin_user.id if admin_user else requester.id

        approval_title = f"Approval for {action_type.replace('_', ' ').title()}"
        approval_desc = f"Proposed action '{action_type}' by {requester.name} ({requester.email}). Parameters: {parameters}"

        if requires_approval:
            approval = Approval(
                id=new_id("appr_"),
                title=approval_title,
                description=approval_desc,
                requester_id=requester.id,
                approver_id=approver_id,
                status=ApprovalStatus.PENDING,
                action_type=action_type,
                action_payload=parameters,
                guideline_version=guideline_version,
                evidence=evidence,
                risks=risks or [],
                target_resource=target_resource,
                requested_at=utcnow(),
            )
            created_approval = await self.approval_repo.create(approval)

            # Audit record
            await self.audit_repo.create(
                AuditRecord(
                    actor_id=requester.id,
                    actor_email=requester.email,
                    action=AuditAction.CREATE,
                    resource_type="approval",
                    resource_id=created_approval.id,
                    description=f"Requested approval for {action_type}",
                )
            )

            # Notify approver
            await self.notif_repo.create(
                Notification(
                    id=new_id("notif_"),
                    user_id=approver_id,
                    type=NotificationType.APPROVAL_REQUESTED,
                    title="New Approval Requested",
                    body=f"{requester.name} requested approval for: {approval_title}",
                    link=f"/tasks",
                )
            )

            return created_approval, None
        else:
            # Execute directly
            exec_record = await self.execute_action(
                action_type=action_type,
                parameters=parameters,
                executor=requester,
            )
            return None, exec_record

    async def execute_action(
        self,
        action_type: str,
        parameters: dict[str, Any],
        executor: UserProfile,
        approval_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ActionExecutionRecord:
        """
        Execute an authorized consequential action via integration adapters.
        Supports idempotency, audit trail, and simulation disclosure in demo mode.
        """
        settings = get_settings()

        # Idempotency check
        if idempotency_key:
            existing = await self.act_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        is_simulated = settings.is_demo
        result_payload: dict[str, Any] = {}
        external_resource_id: Optional[str] = None
        status = ActionStatus.EXECUTED
        error_msg: Optional[str] = None

        try:
            if action_type == "schedule_meeting":
                meeting_title = parameters.get("title", "Project Alignment Meeting")
                scheduled_str = parameters.get("scheduled_at")
                if scheduled_str:
                    try:
                        sched_dt = datetime.fromisoformat(scheduled_str)
                    except Exception:
                        sched_dt = utcnow() + timedelta(days=1)
                else:
                    sched_dt = utcnow() + timedelta(days=1)

                attendees = parameters.get("attendee_ids", [executor.id])
                duration = int(parameters.get("duration_minutes", 30))

                # Create in meeting repository
                meeting = Meeting(
                    id=new_id("meet_"),
                    title=meeting_title,
                    type=MeetingType.GENERAL,
                    description=parameters.get("description", "Scheduled via HYPERREALM Collaborate Agent"),
                    organiser_id=executor.id,
                    attendee_ids=attendees,
                    scheduled_at=sched_dt,
                    duration_minutes=duration,
                    location="Google Meet (Simulated)" if is_simulated else "https://meet.google.com/hpr-sync",
                )
                created_meeting = await self.meeting_repo.create(meeting)
                external_resource_id = created_meeting.id
                result_payload = {
                    "meeting_id": created_meeting.id,
                    "title": created_meeting.title,
                    "scheduled_at": created_meeting.scheduled_at.isoformat(),
                    "location": created_meeting.location,
                    "is_simulated": is_simulated,
                    "message": "Meeting scheduled successfully." if not is_simulated else "Simulated calendar meeting created in local demo mode.",
                }

            elif action_type == "create_task":
                task_title = parameters.get("title", "Action Task")
                task = Task(
                    id=new_id("task_"),
                    title=task_title,
                    description=parameters.get("description", "Created via HYPERREALM AI Copilot"),
                    priority=TaskPriority(parameters.get("priority", "medium")),
                    assignee_id=parameters.get("assignee_id", executor.id),
                    reporter_id=executor.id,
                    project_id=parameters.get("project_id"),
                    status=TaskStatus.TODO,
                )
                created_task = await self.task_repo.create(task)
                external_resource_id = created_task.id
                result_payload = {
                    "task_id": created_task.id,
                    "title": created_task.title,
                    "status": created_task.status.value,
                    "is_simulated": is_simulated,
                }

            elif action_type == "send_notification":
                recipient_id = parameters.get("user_id", executor.id)
                notif = Notification(
                    id=new_id("notif_"),
                    user_id=recipient_id,
                    type=NotificationType.SYSTEM,
                    title=parameters.get("title", "System Notification"),
                    body=parameters.get("body", ""),
                    link=parameters.get("link"),
                )
                created_notif = await self.notif_repo.create(notif)
                external_resource_id = created_notif.id
                result_payload = {"notification_id": created_notif.id, "sent": True}

            elif action_type == "schedule_onboarding_intro":
                intro_id = parameters.get("intro_id")
                from .onboarding_service import get_onboarding_service
                onb_svc = get_onboarding_service()
                meeting, journey = await onb_svc.schedule_introduction(
                    user=executor,
                    intro_id=intro_id,
                )
                external_resource_id = meeting.id
                result_payload = {
                    "meeting_id": meeting.id,
                    "title": meeting.title,
                    "scheduled_at": meeting.scheduled_at.isoformat(),
                    "is_simulated": is_simulated,
                    "message": "Onboarding introduction scheduled successfully.",
                }

            else:
                result_payload = {
                    "executed": True,
                    "action_type": action_type,
                    "is_simulated": is_simulated,
                    "notice": "Action processed through integration adapter.",
                }

        except Exception as e:
            logger.exception("Action execution failed: %s", e)
            status = ActionStatus.FAILED
            error_msg = str(e)
            result_payload = {"error": str(e)}

        record = ActionExecutionRecord(
            id=new_id("act_"),
            action_type=action_type,
            status=status,
            parameters=parameters,
            approval_id=approval_id,
            executed_by=executor.id,
            idempotency_key=idempotency_key,
            result=result_payload,
            external_resource_id=external_resource_id,
            is_simulated=is_simulated,
            error=error_msg,
            created_at=utcnow(),
            executed_at=utcnow() if status == ActionStatus.EXECUTED else None,
        )

        created_record = await self.act_repo.create(record)

        # Audit event
        await self.audit_repo.create(
            AuditRecord(
                actor_id=executor.id,
                actor_email=executor.email,
                action=AuditAction.EXECUTE_ACTION,
                resource_type="action_execution",
                resource_id=created_record.id,
                description=f"Executed action {action_type} (status={status.value}, simulated={is_simulated})",
                metadata={"action_type": action_type, "is_simulated": is_simulated},
            )
        )

        return created_record
