"""
Dependency injection container.

All FastAPI routes obtain repositories and services via these FastAPI
dependency functions so they remain testable and decoupled from the
concrete implementation.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from .config import Settings, get_settings
from .repositories import (
    ActionExecutionRepository,
    ApprovalRepository,
    AuditRepository,
    BrandComplianceRepository,
    ConversationRepository,
    DepartmentRepository,
    DocumentRepository,
    GuidelineRepository,
    GuidelineVersionRepository,
    IncidentRepository,
    LearningRepository,
    MeetingRepository,
    MemoryActionExecutionRepository,
    MemoryApprovalRepository,
    MemoryAuditRepository,
    MemoryBrandComplianceRepository,
    MemoryConversationRepository,
    MemoryDepartmentRepository,
    MemoryDocumentRepository,
    MemoryGuidelineRepository,
    MemoryGuidelineVersionRepository,
    MemoryIncidentRepository,
    MemoryLearningRepository,
    MemoryMeetingRepository,
    MemoryNotificationRepository,
    MemoryOnboardingRepository,
    MemoryProjectRepository,
    MemoryTaskRepository,
    MemoryUserRepository,
    NotificationRepository,
    OnboardingRepository,
    ProjectRepository,
    TaskRepository,
    UserRepository,
)


# ─── Singleton repository instances ───────────────────────────────────────────

_user_repo: UserRepository | None = None
_dept_repo: DepartmentRepository | None = None
_project_repo: ProjectRepository | None = None
_conv_repo: ConversationRepository | None = None
_doc_repo: DocumentRepository | None = None
_guide_repo: GuidelineRepository | None = None
_learning_repo: LearningRepository | None = None
_meeting_repo: MeetingRepository | None = None
_task_repo: TaskRepository | None = None
_approval_repo: ApprovalRepository | None = None
_incident_repo: IncidentRepository | None = None
_notif_repo: NotificationRepository | None = None
_audit_repo: AuditRepository | None = None
_gver_repo: GuidelineVersionRepository | None = None
_bcr_repo: BrandComplianceRepository | None = None
_act_repo: ActionExecutionRepository | None = None
_onb_repo: OnboardingRepository | None = None


def init_repositories(backend: str | None = None, force: bool = False) -> None:
    """
    Called once at startup. Initialises SQLite or in-memory stores.
    """
    global _user_repo, _dept_repo, _project_repo, _conv_repo, _doc_repo
    global _guide_repo, _learning_repo, _meeting_repo, _task_repo
    global _approval_repo, _incident_repo, _notif_repo, _audit_repo
    global _gver_repo, _bcr_repo, _act_repo, _onb_repo

    if not force and _user_repo is not None and backend is None:
        return

    import os
    settings = get_settings()
    active_backend = backend or os.environ.get("REPOSITORY_BACKEND") or settings.REPOSITORY_BACKEND

    if active_backend == "sqlite":
        from .repositories.sqlite import (
            init_sqlite_db,
            SqliteActionExecutionRepository,
            SqliteApprovalRepository,
            SqliteAuditRepository,
            SqliteBrandComplianceRepository,
            SqliteConversationRepository,
            SqliteDepartmentRepository,
            SqliteDocumentRepository,
            SqliteGuidelineRepository,
            SqliteGuidelineVersionRepository,
            SqliteIncidentRepository,
            SqliteLearningRepository,
            SqliteMeetingRepository,
            SqliteNotificationRepository,
            SqliteOnboardingRepository,
            SqliteProjectRepository,
            SqliteTaskRepository,
            SqliteUserRepository,
        )
        init_sqlite_db(settings.SQLITE_DB_PATH)
        _user_repo = SqliteUserRepository(settings.SQLITE_DB_PATH)
        _dept_repo = SqliteDepartmentRepository(settings.SQLITE_DB_PATH)
        _project_repo = SqliteProjectRepository(settings.SQLITE_DB_PATH)
        _conv_repo = SqliteConversationRepository(settings.SQLITE_DB_PATH)
        _doc_repo = SqliteDocumentRepository(settings.SQLITE_DB_PATH)
        _guide_repo = SqliteGuidelineRepository(settings.SQLITE_DB_PATH)
        _learning_repo = SqliteLearningRepository(settings.SQLITE_DB_PATH)
        _meeting_repo = SqliteMeetingRepository(settings.SQLITE_DB_PATH)
        _task_repo = SqliteTaskRepository(settings.SQLITE_DB_PATH)
        _approval_repo = SqliteApprovalRepository(settings.SQLITE_DB_PATH)
        _incident_repo = SqliteIncidentRepository(settings.SQLITE_DB_PATH)
        _notif_repo = SqliteNotificationRepository(settings.SQLITE_DB_PATH)
        _audit_repo = SqliteAuditRepository(settings.SQLITE_DB_PATH)
        _gver_repo = SqliteGuidelineVersionRepository(settings.SQLITE_DB_PATH)
        _bcr_repo = SqliteBrandComplianceRepository(settings.SQLITE_DB_PATH)
        _act_repo = SqliteActionExecutionRepository(settings.SQLITE_DB_PATH)
        _onb_repo = SqliteOnboardingRepository(settings.SQLITE_DB_PATH)
    else:
        if active_backend == "firestore":
            import warnings
            warnings.warn(
                "Firestore backend selected but not yet implemented — falling back to memory",
                stacklevel=1,
            )

        _user_repo = MemoryUserRepository()
        _dept_repo = MemoryDepartmentRepository()
        _project_repo = MemoryProjectRepository()
        _conv_repo = MemoryConversationRepository()
        _doc_repo = MemoryDocumentRepository()
        _guide_repo = MemoryGuidelineRepository()
        _learning_repo = MemoryLearningRepository()
        _meeting_repo = MemoryMeetingRepository()
        _task_repo = MemoryTaskRepository()
        _approval_repo = MemoryApprovalRepository()
        _incident_repo = MemoryIncidentRepository()
        _notif_repo = MemoryNotificationRepository()
        _audit_repo = MemoryAuditRepository()
        _gver_repo = MemoryGuidelineVersionRepository()
        _bcr_repo = MemoryBrandComplianceRepository()
        _act_repo = MemoryActionExecutionRepository()
        _onb_repo = MemoryOnboardingRepository()


# ─── FastAPI dependency functions ─────────────────────────────────────────────

def _ensure_init() -> None:
    if _user_repo is None:
        init_repositories()


def get_user_repo() -> UserRepository:
    _ensure_init()
    assert _user_repo is not None
    return _user_repo


def get_dept_repo() -> DepartmentRepository:
    _ensure_init()
    assert _dept_repo is not None
    return _dept_repo


def get_project_repo() -> ProjectRepository:
    _ensure_init()
    assert _project_repo is not None
    return _project_repo


def get_conv_repo() -> ConversationRepository:
    _ensure_init()
    assert _conv_repo is not None
    return _conv_repo


def get_doc_repo() -> DocumentRepository:
    _ensure_init()
    assert _doc_repo is not None
    return _doc_repo


def get_guide_repo() -> GuidelineRepository:
    _ensure_init()
    assert _guide_repo is not None
    return _guide_repo


def get_learning_repo() -> LearningRepository:
    _ensure_init()
    assert _learning_repo is not None
    return _learning_repo


def get_meeting_repo() -> MeetingRepository:
    _ensure_init()
    assert _meeting_repo is not None
    return _meeting_repo


def get_task_repo() -> TaskRepository:
    _ensure_init()
    assert _task_repo is not None
    return _task_repo


def get_approval_repo() -> ApprovalRepository:
    _ensure_init()
    assert _approval_repo is not None
    return _approval_repo


def get_incident_repo() -> IncidentRepository:
    _ensure_init()
    assert _incident_repo is not None
    return _incident_repo


def get_notif_repo() -> NotificationRepository:
    _ensure_init()
    assert _notif_repo is not None
    return _notif_repo


def get_audit_repo() -> AuditRepository:
    _ensure_init()
    assert _audit_repo is not None
    return _audit_repo


def get_gver_repo() -> GuidelineVersionRepository:
    _ensure_init()
    assert _gver_repo is not None
    return _gver_repo


def get_bcr_repo() -> BrandComplianceRepository:
    _ensure_init()
    assert _bcr_repo is not None
    return _bcr_repo


def get_act_repo() -> ActionExecutionRepository:
    _ensure_init()
    assert _act_repo is not None
    return _act_repo


def get_onboarding_repo() -> OnboardingRepository:
    _ensure_init()
    assert _onb_repo is not None
    return _onb_repo


# ─── Annotated convenience aliases ────────────────────────────────────────────

UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
DeptRepoDep = Annotated[DepartmentRepository, Depends(get_dept_repo)]
ProjectRepoDep = Annotated[ProjectRepository, Depends(get_project_repo)]
ConvRepoDep = Annotated[ConversationRepository, Depends(get_conv_repo)]
DocRepoDep = Annotated[DocumentRepository, Depends(get_doc_repo)]
GuideRepoDep = Annotated[GuidelineRepository, Depends(get_guide_repo)]
LearningRepoDep = Annotated[LearningRepository, Depends(get_learning_repo)]
MeetingRepoDep = Annotated[MeetingRepository, Depends(get_meeting_repo)]
TaskRepoDep = Annotated[TaskRepository, Depends(get_task_repo)]
ApprovalRepoDep = Annotated[ApprovalRepository, Depends(get_approval_repo)]
IncidentRepoDep = Annotated[IncidentRepository, Depends(get_incident_repo)]
NotifRepoDep = Annotated[NotificationRepository, Depends(get_notif_repo)]
AuditRepoDep = Annotated[AuditRepository, Depends(get_audit_repo)]
GuideVersionRepoDep = Annotated[GuidelineVersionRepository, Depends(get_gver_repo)]
BrandComplianceRepoDep = Annotated[BrandComplianceRepository, Depends(get_bcr_repo)]
ActionExecutionRepoDep = Annotated[ActionExecutionRepository, Depends(get_act_repo)]
OnboardingRepoDep = Annotated[OnboardingRepository, Depends(get_onboarding_repo)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
