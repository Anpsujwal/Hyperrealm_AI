"""
Pydantic v2 domain models used throughout HYPERREALM.
These are the canonical data shapes stored/retrieved from the repository.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# ─── Helpers ──────────────────────────────────────────────────────────────────

def new_id(prefix: str = "") -> str:
    uid = str(uuid.uuid4()).replace("-", "")[:16]
    return f"{prefix}{uid}" if prefix else uid


def utcnow() -> datetime:
    return datetime.utcnow()


# ─── Enumerations ─────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "admin"
    TECHNICAL_LEAD = "technical_lead"
    PROJECT_MANAGER = "project_manager"
    SOFTWARE_DEVELOPER = "software_developer"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    EMPLOYEE = "employee"  # generic / default


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class IncidentSeverity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MeetingType(str, Enum):
    STANDUP = "standup"
    SPRINT_PLANNING = "sprint_planning"
    RETROSPECTIVE = "retrospective"
    REVIEW = "review"
    ONE_ON_ONE = "one_on_one"
    GENERAL = "general"


class LearningStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"
    INCIDENT_CREATED = "incident_created"
    MENTION = "mention"
    MEETING_REMINDER = "meeting_reminder"
    SYSTEM = "system"


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAILURE = "auth_failure"
    PERMISSION_DENIED = "permission_denied"


# ─── Core domain models ───────────────────────────────────────────────────────

class Department(BaseModel):
    id: str = Field(default_factory=lambda: new_id("dept_"))
    name: str
    description: str = ""
    head_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    """Full user profile stored server-side. Role is authoritative here."""
    id: str = Field(default_factory=lambda: new_id("usr_"))
    email: EmailStr
    name: str
    role: UserRole = UserRole.EMPLOYEE
    department_id: Optional[str] = None
    department_name: Optional[str] = None  # denormalised for convenience
    job_title: str = ""
    manager_id: Optional[str] = None      # reporting relationship
    avatar_url: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    # hashed password — only set when using local JWT auth (dev mode)
    hashed_password: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    project_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Project(BaseModel):
    id: str = Field(default_factory=lambda: new_id("proj_"))
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    owner_id: str          # user_id of the Technical Lead / PM
    member_ids: list[str] = Field(default_factory=list)
    department_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("conv_"))
    user_id: str
    title: str = "New conversation"
    agent_id: str = "auto"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Message(BaseModel):
    id: str = Field(default_factory=lambda: new_id("msg_"))
    conversation_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    agent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Document(BaseModel):
    id: str = Field(default_factory=lambda: new_id("doc_"))
    title: str
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    author_id: str
    department_id: Optional[str] = None
    is_public: bool = True
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Guideline(BaseModel):
    id: str = Field(default_factory=lambda: new_id("guide_"))
    title: str
    content: str
    category: str  # e.g. "security", "engineering", "hr"
    owner_id: str
    version: str = "1.0"
    status: str = "published"  # "published" | "draft" | "review" | "archived"
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    affected_teams: list[str] = Field(default_factory=list)
    affected_projects: list[str] = Field(default_factory=list)
    changelog: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class LearningResource(BaseModel):
    id: str = Field(default_factory=lambda: new_id("learn_"))
    title: str
    description: str = ""
    category: str  # e.g. "engineering", "security", "leadership"
    url: Optional[str] = None
    estimated_minutes: int = 30
    required_for_roles: list[UserRole] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    due_days: int = 30
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class UserLearningProgress(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ulp_"))
    user_id: str
    resource_id: str
    status: LearningStatus = LearningStatus.NOT_STARTED
    progress_pct: int = 0  # 0-100
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: new_id("meet_"))
    title: str
    type: MeetingType = MeetingType.GENERAL
    description: str = ""
    organiser_id: str
    attendee_ids: list[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    location: str = "Virtual"
    agenda: list[str] = Field(default_factory=list)
    notes: str = ""
    recording_url: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Task(BaseModel):
    id: str = Field(default_factory=lambda: new_id("task_"))
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[str] = None
    reporter_id: str
    project_id: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Approval(BaseModel):
    id: str = Field(default_factory=lambda: new_id("appr_"))
    title: str
    description: str = ""
    requester_id: str
    approver_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    related_task_id: Optional[str] = None
    decision_note: str = ""
    requested_at: datetime = Field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: new_id("inc_"))
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.P3
    status: IncidentStatus = IncidentStatus.OPEN
    reporter_id: str
    assignee_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    resolution_notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Notification(BaseModel):
    id: str = Field(default_factory=lambda: new_id("notif_"))
    user_id: str
    type: NotificationType
    title: str
    body: str = ""
    is_read: bool = False
    link: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("audit_"))
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: AuditAction
    resource_type: str  # e.g. "task", "user", "document"
    resource_id: Optional[str] = None
    description: str = ""
    ip_address: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}
