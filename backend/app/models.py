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
    ARCHITECTURE = "architecture"
    GENERAL = "general"


class MeetingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


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
    MEETING_INVITATION = "meeting_invitation"
    MEETING_ACCEPTED = "meeting_accepted"
    MEETING_REJECTED = "meeting_rejected"
    MEETING_RESCHEDULED = "meeting_rescheduled"
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
    PUBLISH = "publish"
    ARCHIVE = "archive"
    EXECUTE_ACTION = "execute_action"
    COMPLIANCE_AUDIT = "compliance_audit"


class DocumentScope(str, Enum):
    PERSONAL = "personal"
    OFFICIAL = "official"
    PROJECT = "project"
    HISTORICAL = "historical"


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class GuidelineStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY_FOR_REVIEW = "ready_for_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNABLE_TO_DETERMINE = "unable_to_determine"


class ActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


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
    oauth_tokens: dict[str, Any] = Field(default_factory=dict)
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
    # Phase 04 additions
    scope: DocumentScope = DocumentScope.PERSONAL
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: ProcessingStatus = ProcessingStatus.INDEXED
    extracted_text: Optional[str] = None
    tables: list[dict[str, Any]] = Field(default_factory=list)
    images_extracted: list[dict[str, Any]] = Field(default_factory=list)
    visual_analysis_status: Optional[str] = None
    visual_summary: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class Guideline(BaseModel):
    id: str = Field(default_factory=lambda: new_id("guide_"))
    title: str
    content: str
    description: str = ""
    category: str  # e.g. "brand", "security", "engineering", "hr"
    owner_id: str
    version: str = "1.0"
    status: str = "published"  # "published" | "draft" | "processing" | "ready_for_review" | "archived"
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    affected_teams: list[str] = Field(default_factory=list)
    affected_projects: list[str] = Field(default_factory=list)
    changelog: str = ""
    # Phase 04 additions
    applicable_roles: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    applicable_projects: list[str] = Field(default_factory=list)
    processing_status: ProcessingStatus = ProcessingStatus.INDEXED
    access_control: dict[str, Any] = Field(default_factory=dict)
    previous_version_id: Optional[str] = None
    version_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class GuidelineVersionRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("gver_"))
    guideline_id: str
    version: str
    title: str
    content: str
    description: str = ""
    category: str = "general"
    changelog: str = ""
    status: str = "published"
    created_by: str
    effective_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class BrandComplianceReport(BaseModel):
    id: str = Field(default_factory=lambda: new_id("bcr_"))
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    guideline_id: Optional[str] = None
    guideline_version: str = "2.1"
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    summary: str = ""
    checks: list[dict[str, Any]] = Field(default_factory=list)
    observed_evidence: dict[str, Any] = Field(default_factory=dict)
    guideline_reference: str = ""
    severity: str = "none"
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    analysis_status: str = "completed"
    created_by: str = ""
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class ActionExecutionRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("act_"))
    action_type: str
    status: ActionStatus = ActionStatus.EXECUTED
    parameters: dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None
    executed_by: str
    idempotency_key: Optional[str] = None
    result: dict[str, Any] = Field(default_factory=dict)
    external_resource_id: Optional[str] = None
    is_simulated: bool = True
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    executed_at: Optional[datetime] = None

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
    meet_link: Optional[str] = None
    google_event_id: Optional[str] = None
    calendar_provider: str = "local"
    status: MeetingStatus = MeetingStatus.CONFIRMED
    attendee_status: dict[str, str] = Field(default_factory=dict)
    rejection_reason: Optional[str] = None
    proposed_time: Optional[datetime] = None
    rescheduled_by: Optional[str] = None
    reschedule_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class MeetingProposal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("prop_"))
    user_id: str
    user_name: str
    user_email: str
    target_user_id: str
    target_name: str
    target_email: str
    target_role: str = "Subject-Matter Expert"
    title: str
    description: str = ""
    scheduled_at: datetime
    duration_minutes: int = 30
    timezone: str = "IST (UTC+05:30)"
    calendar_status: str = "local"
    availability_checked: bool = True
    availability_note: str = "Availability checked. No collisions detected."
    status: str = "pending_confirmation"  # "pending_confirmation" | "confirmed" | "cancelled" | "expired"
    meeting_id: Optional[str] = None
    meet_link: Optional[str] = None
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
    action_type: Optional[str] = None
    action_payload: dict[str, Any] = Field(default_factory=dict)
    guideline_version: Optional[str] = None
    evidence: str = ""
    risks: list[str] = Field(default_factory=list)
    target_resource: Optional[str] = None
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


# ─── Onboarding domain models ──────────────────────────────────────────────────

class OnboardingStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class OnboardingFormStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class OnboardingCourseItem(BaseModel):
    resource_id: str
    title: str
    description: str = ""
    category: str = "engineering"
    estimated_minutes: int = 60
    is_mandatory: bool = False
    requires_approval: bool = False
    approval_status: str = "not_required"  # "not_required" | "pending_approval" | "approved" | "rejected"
    approval_id: Optional[str] = None
    sequence_order: int = 1
    status: LearningStatus = LearningStatus.NOT_STARTED
    progress_pct: int = 0
    reason: str = ""

    model_config = {"from_attributes": True}


class OnboardingIntroduction(BaseModel):
    id: str = Field(default_factory=lambda: new_id("intro_"))
    person_id: str
    person_name: str
    role: str
    email: str
    avatar_url: Optional[str] = None
    relationship: str = "Team Member"  # "Manager" | "Assigned Buddy" | "Squad Teammate" | "Department Stakeholder"
    meeting_purpose: str = "Introductory alignment and onboarding support"
    status: str = "unassigned"  # "unassigned" | "scheduled" | "completed"
    meeting_id: Optional[str] = None

    model_config = {"from_attributes": True}


class OnboardingFormRequirement(BaseModel):
    id: str  # e.g. "form_i9_identity"
    title: str
    description: str
    category: str = "compliance"  # "legal" | "payroll" | "compliance" | "security"
    is_sensitive: bool = False
    status: OnboardingFormStatus = OnboardingFormStatus.PENDING
    due_days: int = 7
    due_date: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    prepopulated_fields: dict[str, Any] = Field(default_factory=dict)
    submitted_data: dict[str, Any] = Field(default_factory=dict)
    feedback_notes: str = ""

    model_config = {"from_attributes": True}


class OnboardingMilestone(BaseModel):
    id: str
    title: str
    phase: str  # "Day 1" | "Week 1" | "Month 1"
    due_days: int
    items: list[str] = Field(default_factory=list)
    status: OnboardingStepStatus = OnboardingStepStatus.PENDING

    model_config = {"from_attributes": True}


class OnboardingJourney(BaseModel):
    id: str = Field(default_factory=lambda: new_id("onb_"))
    user_id: str
    user_name: Optional[str] = None
    role: str
    department: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    buddy_id: Optional[str] = None
    buddy_name: Optional[str] = None
    start_date: datetime = Field(default_factory=utcnow)
    completion_pct: int = 0
    learning_completion_pct: int = 0
    forms_completion_pct: int = 0
    intros_completion_pct: int = 0
    status: str = "in_progress"  # "in_progress" | "completed" | "blocked"
    courses: list[OnboardingCourseItem] = Field(default_factory=list)
    introductions: list[OnboardingIntroduction] = Field(default_factory=list)
    forms: list[OnboardingFormRequirement] = Field(default_factory=list)
    onboarding_steps: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_action: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}

