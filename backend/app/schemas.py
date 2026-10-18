"""
Pydantic v2 request/response schemas (DTOs).
Kept separate from domain models to control what the API exposes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field

from .models import (
    ActionStatus,
    ApprovalStatus,
    AuditAction,
    ComplianceStatus,
    DocumentScope,
    GuidelineStatus,
    IncidentSeverity,
    IncidentStatus,
    LearningStatus,
    MeetingStatus,
    MeetingType,
    NotificationType,
    ProcessingStatus,
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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Guidelines ───────────────────────────────────────────────────────────────

class GuidelineCreate(BaseModel):
    title: str
    content: str
    description: str = ""
    category: str
    version: str = "1.0"
    status: str = "published"
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    affected_teams: list[str] = Field(default_factory=list)
    affected_projects: list[str] = Field(default_factory=list)
    changelog: str = ""
    applicable_roles: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    applicable_projects: list[str] = Field(default_factory=list)


class GuidelineUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    affected_teams: Optional[list[str]] = None
    affected_projects: Optional[list[str]] = None
    changelog: Optional[str] = None
    applicable_roles: Optional[list[str]] = None
    applicable_departments: Optional[list[str]] = None
    applicable_projects: Optional[list[str]] = None


class GuidelineOut(BaseModel):
    id: str
    title: str
    content: str
    description: str = ""
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
    applicable_roles: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    applicable_projects: list[str] = Field(default_factory=list)
    processing_status: ProcessingStatus = ProcessingStatus.INDEXED
    access_control: dict[str, Any] = Field(default_factory=dict)
    version_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Phase 04 Knowledge Hub & Document Intelligence Schemas ───────────────────

class DocumentSummaryRequest(BaseModel):
    focus_areas: list[str] = Field(default_factory=list)


class DocumentSummaryResponse(BaseModel):
    document_id: str
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    visual_elements_detected: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    entities_detected: list[str] = Field(default_factory=list)
    visual_elements_summary: Optional[str] = None
    scope: DocumentScope = DocumentScope.PERSONAL


class DocumentQueryRequest(BaseModel):
    query: str


class DocumentQueryResponse(BaseModel):
    document_id: str
    query: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.95
    scope: DocumentScope = DocumentScope.PERSONAL


class KnowledgeSearchRequest(BaseModel):
    query: str
    scopes: list[DocumentScope] = Field(
        default_factory=lambda: [DocumentScope.PERSONAL, DocumentScope.OFFICIAL]
    )
    top_k: int = 5


class KnowledgeSearchResult(BaseModel):
    id: str
    title: str
    snippet: str
    scope: DocumentScope
    category: str
    version: str = "1.0"
    author_id: str
    score: float
    citations: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
    total_results: int
    discrepancies: list[str] = Field(default_factory=list)


class BrandComplianceAuditRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_filename: Optional[str] = None
    guideline_id: Optional[str] = None
    document_id: Optional[str] = None


class BrandComplianceAuditResponse(BaseModel):
    id: str
    status: ComplianceStatus
    summary: str
    guideline_version: str = "2.1"
    checks: list[dict[str, Any]] = Field(default_factory=list)
    observed_evidence: dict[str, Any] = Field(default_factory=dict)
    guideline_reference: str = ""
    severity: str = "none"
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    analysis_status: str = "completed"
    created_at: datetime

    model_config = {"from_attributes": True}


class GuidelineVersionCreate(BaseModel):
    version: str
    title: str
    content: str
    description: str = ""
    changelog: str = ""
    effective_date: Optional[datetime] = None
    status: str = "published"


class GuidelineVersionOut(BaseModel):
    id: str
    guideline_id: str
    version: str
    title: str
    content: str
    description: str = ""
    changelog: str = ""
    status: str
    created_by: str
    effective_date: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class DiffLine(BaseModel):
    type: str  # 'added' | 'removed' | 'unchanged'
    text: str
    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None


class SideBySideLine(BaseModel):
    old_line_no: Optional[int] = None
    old_text: Optional[str] = None
    old_type: Optional[str] = None  # 'removed' | 'unchanged' | 'empty'
    new_line_no: Optional[int] = None
    new_text: Optional[str] = None
    new_type: Optional[str] = None  # 'added' | 'unchanged' | 'empty'


class SemanticChangeSummary(BaseModel):
    change_type: str  # 'breaking' | 'enhancement' | 'deprecation' | 'requirement'
    category: str
    description: str


class GuidelineDiffResponse(BaseModel):
    guideline_id: str
    guideline_title: str
    category: str
    base_version: str
    target_version: str
    available_versions: list[str] = Field(default_factory=list)
    impact_badges: list[str] = Field(default_factory=list)
    impacted_roles: list[str] = Field(default_factory=list)
    impacted_departments: list[str] = Field(default_factory=list)
    impacted_projects: list[str] = Field(default_factory=list)
    severity: str = "medium"  # "high" | "medium" | "low"
    semantic_summary: list[SemanticChangeSummary] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
    unified_diff: list[DiffLine] = Field(default_factory=list)
    side_by_side: list[SideBySideLine] = Field(default_factory=list)



class ChatOrchestratorRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = "auto"
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ChatOrchestratorResponse(BaseModel):
    conversation_id: str
    agent_id: str
    agent_name: str
    response: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    discrepancy_notice: Optional[str] = None
    compliance_report: Optional[BrandComplianceAuditResponse] = None
    proposed_actions: list[dict[str, Any]] = Field(default_factory=list)
    workflow_status: Optional[str] = None
    is_simulated: bool = False
    model_used: str = "gemini-2.5-flash"
    delegated_agents: list[str] = Field(default_factory=list)


class ActionExecutionRequest(BaseModel):
    action_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ActionExecutionResponse(BaseModel):
    id: str
    action_type: str
    status: ActionStatus
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    external_resource_id: Optional[str] = None
    is_simulated: bool = True
    executed_at: Optional[datetime] = None

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
    force: bool = False


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
    organiser_name: Optional[str] = None
    attendee_ids: list[str]
    attendee_names: dict[str, str] = Field(default_factory=dict)
    project_id: Optional[str]
    scheduled_at: datetime
    duration_minutes: int
    location: str
    agenda: list[str]
    notes: str
    recording_url: Optional[str]
    meet_link: Optional[str] = None
    google_event_id: Optional[str] = None
    calendar_provider: Optional[str] = "local"
    status: MeetingStatus = MeetingStatus.CONFIRMED
    attendee_status: dict[str, str] = Field(default_factory=dict)
    rejection_reason: Optional[str] = None
    proposed_time: Optional[datetime] = None
    rescheduled_by: Optional[str] = None
    reschedule_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingConflict(BaseModel):
    meeting_id: str
    title: str
    scheduled_at: datetime
    duration_minutes: int
    conflicting_user_ids: list[str] = Field(default_factory=list)
    conflicting_user_names: list[str] = Field(default_factory=list)


class CalendarAvailabilityRequest(BaseModel):
    scheduled_at: datetime
    duration_minutes: int = 30
    attendee_ids: list[str] = Field(default_factory=list)
    exclude_meeting_id: Optional[str] = None


class CalendarAvailabilityResponse(BaseModel):
    available: bool
    conflicts: list[MeetingConflict] = Field(default_factory=list)
    suggested_slots: list[datetime] = Field(default_factory=list)
    message: str = ""


class MeetingProposalOut(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    target_user_id: str
    target_name: str
    target_email: str
    target_role: str
    title: str
    description: str = ""
    scheduled_at: datetime
    scheduled_at_ist: str = ""
    duration_minutes: int = 30
    timezone: str = "IST (UTC+05:30)"
    calendar_status: str
    availability_checked: bool
    availability_note: str
    status: str
    meeting_id: Optional[str] = None
    meet_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingProposalCreate(BaseModel):
    target_user_id: str
    title: str
    description: str = ""
    scheduled_at: datetime
    duration_minutes: int = 30


class MeetingProposalUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None


class MeetingProposalConfirm(BaseModel):
    idempotency_key: Optional[str] = None


class MeetingRsvpRequest(BaseModel):
    action: str  # "accept" or "reject"
    rejection_reason: Optional[str] = None
    proposed_time: Optional[datetime] = None


class MeetingRsvpResponse(BaseModel):
    success: bool
    action: str
    meeting: MeetingOut
    message: str
    auto_rescheduled: bool = False


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
    action_type: Optional[str] = None
    action_payload: dict[str, Any] = Field(default_factory=dict)
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


# ─── Onboarding schemas ────────────────────────────────────────────────────────

class OnboardingCourseItemOut(BaseModel):
    resource_id: str
    title: str
    description: str = ""
    category: str = "engineering"
    estimated_minutes: int = 60
    is_mandatory: bool = False
    requires_approval: bool = False
    approval_status: str = "not_required"
    approval_id: Optional[str] = None
    sequence_order: int = 1
    status: str = "not_started"
    progress_pct: int = 0
    reason: str = ""

    model_config = {"from_attributes": True}


class OnboardingIntroductionOut(BaseModel):
    id: str
    person_id: str
    person_name: str
    role: str
    email: str
    avatar_url: Optional[str] = None
    relationship: str = "Team Member"
    meeting_purpose: str = "Introductory alignment and onboarding support"
    status: str = "unassigned"
    meeting_id: Optional[str] = None

    model_config = {"from_attributes": True}


class OnboardingFormRequirementOut(BaseModel):
    id: str
    title: str
    description: str
    category: str = "compliance"
    is_sensitive: bool = False
    status: str = "pending"
    due_days: int = 7
    due_date: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    prepopulated_fields: dict[str, Any] = Field(default_factory=dict)
    submitted_data: dict[str, Any] = Field(default_factory=dict)
    feedback_notes: str = ""

    model_config = {"from_attributes": True}


class OnboardingJourneyOut(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    role: str
    department: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    buddy_id: Optional[str] = None
    buddy_name: Optional[str] = None
    start_date: datetime
    completion_pct: int = 0
    learning_completion_pct: int = 0
    forms_completion_pct: int = 0
    intros_completion_pct: int = 0
    status: str = "in_progress"
    courses: list[OnboardingCourseItemOut] = Field(default_factory=list)
    introductions: list[OnboardingIntroductionOut] = Field(default_factory=list)
    forms: list[OnboardingFormRequirementOut] = Field(default_factory=list)
    onboarding_steps: list[dict[str, Any]] = Field(default_factory=list)
    onboardingSteps: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_action: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OnboardingApprovalRequest(BaseModel):
    course_ids: list[str]
    justification: str = "Role specialization and squad project alignment"


class OnboardingApprovalResolveRequest(BaseModel):
    status: str  # "approved" | "rejected"
    decision_note: str = ""
    approved_course_ids: Optional[list[str]] = None


class OnboardingFormSubmitRequest(BaseModel):
    form_data: dict[str, Any]
    signature_confirmation: bool = True


class OnboardingScheduleIntroRequest(BaseModel):
    intro_id: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 30
    notes: str = ""

