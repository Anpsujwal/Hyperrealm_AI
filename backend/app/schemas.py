"""
Pydantic v2 request/response schemas (DTOs).
Kept separate from domain models to control what the API exposes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field

from .models import (
    ApprovalStatus,
    AuditAction,
    IncidentSeverity,
    IncidentStatus,
    LearningStatus,
    MeetingType,
    NotificationType,
    TaskPriority,
    TaskStatus,
    UserRole,
    UserStatus,
)

T = TypeVar("T")


# ─── Shared ───────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated envelope."""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserPublic"


class FirebaseTokenRequest(BaseModel):
    """Exchange a Firebase identity token for a backend session token."""
    id_token: str


# ─── Users ────────────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    """Safe user representation returned in API responses."""
    id: str
    email: EmailStr
    name: str
    role: UserRole
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    job_title: str
    manager_id: Optional[str] = None
    avatar_url: Optional[str] = None
    status: UserStatus
    skills: list[str]
    project_ids: list[str]
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserSensitive(BaseModel):
    """Sensitive employee details restricted to Admins, direct line managers, or self."""
    id: str
    email: EmailStr
    name: str
    role: UserRole
    department_name: Optional[str] = None
    job_title: str
    manager_id: Optional[str] = None
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    employee_code: str = "EMP-HYPER"
    clearance_level: str = "Internal Standard"
    performance_rating: str = "Exceeds Expectations"
    onboarding_status: str = "Completed"
    contract_type: str = "Full-time Permanent"
    emergency_contact: str = "+1 (555) 019-2834"
    salary_band: str = "L4 / Tier 1"

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.EMPLOYEE
    department_id: Optional[str] = None
    job_title: str = ""
    manager_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    department_id: Optional[str] = None
    job_title: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[UserStatus] = None
    skills: Optional[list[str]] = None
    avatar_url: Optional[str] = None


# ─── Departments ──────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str
    description: str = ""
    head_user_id: Optional[str] = None


class DepartmentOut(BaseModel):
    id: str
    name: str
    description: str
    head_user_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Projects ─────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    owner_id: str
    department_id: Optional[str] = None
    member_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[str] = None
    member_ids: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    end_date: Optional[datetime] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    owner_id: str
    member_ids: list[str]
    department_id: Optional[str]
    tags: list[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Conversations & Messages ─────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: str = "New conversation"
    agent_id: str = "auto"


class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: str
    agent_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    role: str = "user"
    content: str
    agent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    agent_id: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Documents ────────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    department_id: Optional[str] = None
    is_public: bool = True


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    department_id: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentOut(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: list[str]
    author_id: str
    department_id: Optional[str]
    is_public: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Guidelines ───────────────────────────────────────────────────────────────

class GuidelineCreate(BaseModel):
    title: str
    content: str
    category: str
    version: str = "1.0"
    status: str = "published"
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    affected_teams: list[str] = Field(default_factory=list)
    affected_projects: list[str] = Field(default_factory=list)
    changelog: str = ""


class GuidelineUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    affected_teams: Optional[list[str]] = None
    affected_projects: Optional[list[str]] = None
    changelog: Optional[str] = None


class GuidelineOut(BaseModel):
    id: str
    title: str
    content: str
    category: str
    owner_id: str
    version: str = "1.0"
    status: str = "published"
    effective_date: Optional[datetime]
    review_date: Optional[datetime]
    tags: list[str]
    affected_teams: list[str] = Field(default_factory=list)
    affected_projects: list[str] = Field(default_factory=list)
    changelog: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Learning ─────────────────────────────────────────────────────────────────

class LearningResourceCreate(BaseModel):
    title: str
    description: str = ""
    category: str
    url: Optional[str] = None
    estimated_minutes: int = 30
    required_for_roles: list[UserRole] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    due_days: int = 30


class LearningResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    estimated_minutes: Optional[int] = None
    required_for_roles: Optional[list[UserRole]] = None
    tags: Optional[list[str]] = None
    prerequisites: Optional[list[str]] = None
    due_days: Optional[int] = None


class LearningResourceOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    url: Optional[str]
    estimated_minutes: int
    required_for_roles: list[UserRole]
    tags: list[str]
    prerequisites: list[str] = Field(default_factory=list)
    due_days: int = 30
    created_at: datetime

    model_config = {"from_attributes": True}


class LearningProgressUpdate(BaseModel):
    status: LearningStatus
    progress_pct: int = Field(ge=0, le=100)


class LearningProgressOut(BaseModel):
    id: str
    user_id: str
    resource_id: str
    status: LearningStatus
    progress_pct: int
    due_date: Optional[datetime] = None
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Meetings ─────────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    type: MeetingType = MeetingType.GENERAL
    description: str = ""
    attendee_ids: list[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    location: str = "Virtual"
    agenda: list[str] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    attendee_ids: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    agenda: Optional[list[str]] = None
    notes: Optional[str] = None
    recording_url: Optional[str] = None


class MeetingOut(BaseModel):
    id: str
    title: str
    type: MeetingType
    description: str
    organiser_id: str
    attendee_ids: list[str]
    project_id: Optional[str]
    scheduled_at: datetime
    duration_minutes: int
    location: str
    agenda: list[str]
    notes: str
    recording_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Tasks ────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[str] = None
    project_id: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[str]
    reporter_id: str
    project_id: Optional[str]
    due_date: Optional[datetime]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Approvals ────────────────────────────────────────────────────────────────

class ApprovalCreate(BaseModel):
    title: str
    description: str = ""
    approver_id: str
    related_task_id: Optional[str] = None


class ApprovalResolve(BaseModel):
    status: ApprovalStatus  # approved | rejected
    decision_note: str = ""


class ApprovalOut(BaseModel):
    id: str
    title: str
    description: str
    requester_id: str
    approver_id: str
    status: ApprovalStatus
    related_task_id: Optional[str]
    decision_note: str
    requested_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Incidents ────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.P3
    project_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    assignee_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: Optional[list[str]] = None


class IncidentOut(BaseModel):
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    reporter_id: str
    assignee_id: Optional[str]
    project_id: Optional[str]
    tags: list[str]
    resolution_notes: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    is_read: bool
    link: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditRecordOut(BaseModel):
    id: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    description: str
    ip_address: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Org chart ────────────────────────────────────────────────────────────────

class OrgNode(BaseModel):
    user: UserPublic
    reports: list["OrgNode"] = Field(default_factory=list)
