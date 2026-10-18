"""
HYPERREALM Firestore Repository Implementation.
Provides Google Cloud Firestore persistence when FIRESTORE_ENABLED=true or
REPOSITORY_BACKEND=firestore.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from ..config import get_settings
from ..models import (
    ActionExecutionRecord,
    Approval,
    AuditRecord,
    BrandComplianceReport,
    Conversation,
    Department,
    Document,
    DocumentScope,
    Guideline,
    GuidelineVersionRecord,
    Incident,
    LearningResource,
    Meeting,
    Message,
    Notification,
    OnboardingJourney,
    Project,
    Task,
    UserLearningProgress,
    UserProfile,
    UserRole,
    utcnow,
)
from .base import (
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
    NotificationRepository,
    OnboardingRepository,
    ProjectRepository,
    TaskRepository,
    UserRepository,
)

logger = logging.getLogger("hyperrealm.repositories.firestore")

T = TypeVar("T", bound=BaseModel)


def get_firestore_client():
    settings = get_settings()
    if settings.GOOGLE_APPLICATION_CREDENTIALS and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
    from google.cloud import firestore
    project = settings.GOOGLE_CLOUD_PROJECT or None
    database = settings.FIRESTORE_DATABASE_ID or "(default)"
    return firestore.Client(project=project, database=database)


def _to_firestore_dict(model: BaseModel) -> dict[str, Any]:
    """Serialize model to Firestore compatible dictionary."""
    data = model.model_dump(mode="json")
    return data


def _from_firestore_dict(model_cls: Type[T], data: dict[str, Any]) -> T:
    """Deserialize dictionary into typed model."""
    return model_cls.model_validate(data)


# ─── Firestore Repositories ──────────────────────────────────────────────────

class FirestoreUserRepository(UserRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("users")

    async def get(self, user_id: str) -> Optional[UserProfile]:
        doc = await asyncio.to_thread(self.col.document(user_id).get)
        if doc.exists:
            return _from_firestore_dict(UserProfile, doc.to_dict())
        return None

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        def _query():
            docs = list(self.col.where("email", "==", email.lower().strip()).limit(1).stream())
            return docs[0].to_dict() if docs else None
        data = await asyncio.to_thread(_query)
        return _from_firestore_dict(UserProfile, data) if data else None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[UserProfile], int]:
        def _query():
            docs = list(self.col.stream())
            total = len(docs)
            page = docs[skip:skip + limit]
            return [_from_firestore_dict(UserProfile, d.to_dict()) for d in page], total
        return await asyncio.to_thread(_query)

    async def create(self, user: UserProfile) -> UserProfile:
        await asyncio.to_thread(self.col.document(user.id).set, _to_firestore_dict(user))
        return user

    async def update(self, user: UserProfile) -> UserProfile:
        await asyncio.to_thread(self.col.document(user.id).set, _to_firestore_dict(user), merge=True)
        return user

    async def delete(self, user_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(user_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(user_id).delete)
            return True
        return False

    async def list_reports(self, manager_id: str) -> list[UserProfile]:
        def _query():
            docs = list(self.col.where("manager_id", "==", manager_id).stream())
            return [_from_firestore_dict(UserProfile, d.to_dict()) for d in docs]
        return await asyncio.to_thread(_query)


class FirestoreDepartmentRepository(DepartmentRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("departments")

    async def get(self, dept_id: str) -> Optional[Department]:
        doc = await asyncio.to_thread(self.col.document(dept_id).get)
        return _from_firestore_dict(Department, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        def _query():
            docs = list(self.col.stream())
            total = len(docs)
            return [_from_firestore_dict(Department, d.to_dict()) for d in docs[skip:skip + limit]], total
        return await asyncio.to_thread(_query)

    async def create(self, dept: Department) -> Department:
        await asyncio.to_thread(self.col.document(dept.id).set, _to_firestore_dict(dept))
        return dept

    async def update(self, dept: Department) -> Department:
        await asyncio.to_thread(self.col.document(dept.id).set, _to_firestore_dict(dept), merge=True)
        return dept


class FirestoreProjectRepository(ProjectRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("projects")

    async def get(self, project_id: str) -> Optional[Project]:
        doc = await asyncio.to_thread(self.col.document(project_id).get)
        return _from_firestore_dict(Project, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Project], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Project, d.to_dict()) for d in docs]
            if user_id:
                items = [p for p in items if p.owner_id == user_id or user_id in p.member_ids]
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, project: Project) -> Project:
        await asyncio.to_thread(self.col.document(project.id).set, _to_firestore_dict(project))
        return project

    async def update(self, project: Project) -> Project:
        await asyncio.to_thread(self.col.document(project.id).set, _to_firestore_dict(project), merge=True)
        return project

    async def delete(self, project_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(project_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(project_id).delete)
            return True
        return False


class FirestoreConversationRepository(ConversationRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("conversations")
        self.msg_col = self.client.collection("messages")

    async def get(self, conv_id: str) -> Optional[Conversation]:
        doc = await asyncio.to_thread(self.col.document(conv_id).get)
        return _from_firestore_dict(Conversation, doc.to_dict()) if doc.exists else None

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Conversation], int]:
        def _query():
            docs = list(self.col.where("user_id", "==", user_id).stream())
            items = sorted([_from_firestore_dict(Conversation, d.to_dict()) for d in docs], key=lambda c: c.updated_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, conv: Conversation) -> Conversation:
        await asyncio.to_thread(self.col.document(conv.id).set, _to_firestore_dict(conv))
        return conv

    async def update(self, conv: Conversation) -> Conversation:
        await asyncio.to_thread(self.col.document(conv.id).set, _to_firestore_dict(conv), merge=True)
        return conv

    async def delete(self, conv_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(conv_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(conv_id).delete)
            return True
        return False

    async def list_messages(self, conv_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Message], int]:
        def _query():
            docs = list(self.msg_col.where("conversation_id", "==", conv_id).stream())
            items = sorted([_from_firestore_dict(Message, d.to_dict()) for d in docs], key=lambda m: m.created_at)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def add_message(self, message: Message) -> Message:
        await asyncio.to_thread(self.msg_col.document(message.id).set, _to_firestore_dict(message))
        return message


class FirestoreDocumentRepository(DocumentRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("documents")

    async def get(self, doc_id: str) -> Optional[Document]:
        doc = await asyncio.to_thread(self.col.document(doc_id).get)
        return _from_firestore_dict(Document, doc.to_dict()) if doc.exists else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        author_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Document, d.to_dict()) for d in docs]
            if category:
                items = [d for d in items if d.category == category]
            if author_id:
                items = [d for d in items if d.author_id == author_id]
            if scope:
                items = [d for d in items if getattr(d.scope, "value", str(d.scope)) == scope]
            items.sort(key=lambda d: d.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, doc: Document) -> Document:
        await asyncio.to_thread(self.col.document(doc.id).set, _to_firestore_dict(doc))
        return doc

    async def update(self, doc: Document) -> Document:
        await asyncio.to_thread(self.col.document(doc.id).set, _to_firestore_dict(doc), merge=True)
        return doc

    async def delete(self, doc_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(doc_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(doc_id).delete)
            return True
        return False


class FirestoreGuidelineRepository(GuidelineRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("guidelines")

    async def get(self, guide_id: str) -> Optional[Guideline]:
        doc = await asyncio.to_thread(self.col.document(guide_id).get)
        return _from_firestore_dict(Guideline, doc.to_dict()) if doc.exists else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Guideline], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Guideline, d.to_dict()) for d in docs]
            if category:
                items = [g for g in items if g.category == category]
            if status:
                items = [g for g in items if getattr(g.status, "value", str(g.status)) == status]
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, guide: Guideline) -> Guideline:
        await asyncio.to_thread(self.col.document(guide.id).set, _to_firestore_dict(guide))
        return guide

    async def update(self, guide: Guideline) -> Guideline:
        await asyncio.to_thread(self.col.document(guide.id).set, _to_firestore_dict(guide), merge=True)
        return guide

    async def delete(self, guide_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(guide_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(guide_id).delete)
            return True
        return False


class FirestoreLearningRepository(LearningRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.res_col = self.client.collection("learning_resources")
        self.prog_col = self.client.collection("learning_progress")

    async def get_resource(self, resource_id: str) -> Optional[LearningResource]:
        doc = await asyncio.to_thread(self.res_col.document(resource_id).get)
        return _from_firestore_dict(LearningResource, doc.to_dict()) if doc.exists else None

    async def list_resources(self, skip: int = 0, limit: int = 20) -> tuple[list[LearningResource], int]:
        def _query():
            docs = list(self.res_col.stream())
            total = len(docs)
            return [_from_firestore_dict(LearningResource, d.to_dict()) for d in docs[skip:skip + limit]], total
        return await asyncio.to_thread(_query)

    async def create_resource(self, resource: LearningResource) -> LearningResource:
        await asyncio.to_thread(self.res_col.document(resource.id).set, _to_firestore_dict(resource))
        return resource

    async def get_progress(self, user_id: str, resource_id: str) -> Optional[UserLearningProgress]:
        doc_id = f"{user_id}_{resource_id}"
        doc = await asyncio.to_thread(self.prog_col.document(doc_id).get)
        return _from_firestore_dict(UserLearningProgress, doc.to_dict()) if doc.exists else None

    async def list_progress_by_user(self, user_id: str) -> list[UserLearningProgress]:
        def _query():
            docs = list(self.prog_col.where("user_id", "==", user_id).stream())
            return [_from_firestore_dict(UserLearningProgress, d.to_dict()) for d in docs]
        return await asyncio.to_thread(_query)

    async def upsert_progress(self, progress: UserLearningProgress) -> UserLearningProgress:
        doc_id = f"{progress.user_id}_{progress.resource_id}"
        await asyncio.to_thread(self.prog_col.document(doc_id).set, _to_firestore_dict(progress), merge=True)
        return progress


class FirestoreMeetingRepository(MeetingRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("meetings")

    async def get(self, meeting_id: str) -> Optional[Meeting]:
        doc = await asyncio.to_thread(self.col.document(meeting_id).get)
        return _from_firestore_dict(Meeting, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Meeting], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Meeting, d.to_dict()) for d in docs]
            if user_id:
                items = [m for m in items if m.organiser_id == user_id or user_id in m.attendee_ids]
            items.sort(key=lambda m: m.scheduled_at)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, meeting: Meeting) -> Meeting:
        await asyncio.to_thread(self.col.document(meeting.id).set, _to_firestore_dict(meeting))
        return meeting

    async def update(self, meeting: Meeting) -> Meeting:
        await asyncio.to_thread(self.col.document(meeting.id).set, _to_firestore_dict(meeting), merge=True)
        return meeting

    async def delete(self, meeting_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(meeting_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(meeting_id).delete)
            return True
        return False


class FirestoreTaskRepository(TaskRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("tasks")

    async def get(self, task_id: str) -> Optional[Task]:
        doc = await asyncio.to_thread(self.col.document(task_id).get)
        return _from_firestore_dict(Task, doc.to_dict()) if doc.exists else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        assignee_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Task], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Task, d.to_dict()) for d in docs]
            if assignee_id:
                items = [t for t in items if t.assignee_id == assignee_id]
            if project_id:
                items = [t for t in items if t.project_id == project_id]
            if status:
                items = [t for t in items if getattr(t.status, "value", str(t.status)) == status]
            items.sort(key=lambda t: t.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, task: Task) -> Task:
        await asyncio.to_thread(self.col.document(task.id).set, _to_firestore_dict(task))
        return task

    async def update(self, task: Task) -> Task:
        await asyncio.to_thread(self.col.document(task.id).set, _to_firestore_dict(task), merge=True)
        return task

    async def delete(self, task_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(task_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(task_id).delete)
            return True
        return False


class FirestoreApprovalRepository(ApprovalRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("approvals")

    async def get(self, approval_id: str) -> Optional[Approval]:
        doc = await asyncio.to_thread(self.col.document(approval_id).get)
        return _from_firestore_dict(Approval, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, approver_id: Optional[str] = None, status: Optional[str] = None) -> tuple[list[Approval], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Approval, d.to_dict()) for d in docs]
            if approver_id:
                items = [a for a in items if a.approver_id == approver_id]
            if status:
                items = [a for a in items if getattr(a.status, "value", str(a.status)) == status]
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, approval: Approval) -> Approval:
        await asyncio.to_thread(self.col.document(approval.id).set, _to_firestore_dict(approval))
        return approval

    async def update(self, approval: Approval) -> Approval:
        await asyncio.to_thread(self.col.document(approval.id).set, _to_firestore_dict(approval), merge=True)
        return approval


class FirestoreAuditRepository(AuditRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("audit_records")

    async def get(self, record_id: str) -> Optional[AuditRecord]:
        doc = await asyncio.to_thread(self.col.document(record_id).get)
        return _from_firestore_dict(AuditRecord, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 50, actor_id: Optional[str] = None, resource_type: Optional[str] = None) -> tuple[list[AuditRecord], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(AuditRecord, d.to_dict()) for d in docs]
            if actor_id:
                items = [a for a in items if a.actor_id == actor_id]
            if resource_type:
                items = [a for a in items if a.resource_type == resource_type]
            items.sort(key=lambda a: a.timestamp, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, record: AuditRecord) -> AuditRecord:
        await asyncio.to_thread(self.col.document(record.id).set, _to_firestore_dict(record))
        return record


class FirestoreNotificationRepository(NotificationRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("notifications")

    async def get(self, notification_id: str) -> Optional[Notification]:
        doc = await asyncio.to_thread(self.col.document(notification_id).get)
        return _from_firestore_dict(Notification, doc.to_dict()) if doc.exists else None

    async def list(self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20) -> tuple[list[Notification], int]:
        def _query():
            docs = list(self.col.where("user_id", "==", user_id).stream())
            items = [_from_firestore_dict(Notification, d.to_dict()) for d in docs]
            if unread_only:
                items = [n for n in items if not n.is_read]
            items.sort(key=lambda n: n.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, notification: Notification) -> Notification:
        await asyncio.to_thread(self.col.document(notification.id).set, _to_firestore_dict(notification))
        return notification

    async def update(self, notification: Notification) -> Notification:
        await asyncio.to_thread(self.col.document(notification.id).set, _to_firestore_dict(notification), merge=True)
        return notification

    async def delete(self, notification_id: str) -> bool:
        doc = await asyncio.to_thread(self.col.document(notification_id).get)
        if doc.exists:
            await asyncio.to_thread(self.col.document(notification_id).delete)
            return True
        return False


class FirestoreIncidentRepository(IncidentRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("incidents")

    async def get(self, incident_id: str) -> Optional[Incident]:
        doc = await asyncio.to_thread(self.col.document(incident_id).get)
        return _from_firestore_dict(Incident, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, status: Optional[str] = None) -> tuple[list[Incident], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(Incident, d.to_dict()) for d in docs]
            if status:
                items = [i for i in items if getattr(i.status, "value", str(i.status)) == status]
            items.sort(key=lambda i: i.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, incident: Incident) -> Incident:
        await asyncio.to_thread(self.col.document(incident.id).set, _to_firestore_dict(incident))
        return incident

    async def update(self, incident: Incident) -> Incident:
        await asyncio.to_thread(self.col.document(incident.id).set, _to_firestore_dict(incident), merge=True)
        return incident


class FirestoreOnboardingRepository(OnboardingRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("onboarding_journeys")

    async def get(self, journey_id: str) -> Optional[OnboardingJourney]:
        doc = await asyncio.to_thread(self.col.document(journey_id).get)
        return _from_firestore_dict(OnboardingJourney, doc.to_dict()) if doc.exists else None

    async def get_by_user(self, user_id: str) -> Optional[OnboardingJourney]:
        def _query():
            docs = list(self.col.where("user_id", "==", user_id).limit(1).stream())
            return docs[0].to_dict() if docs else None
        data = await asyncio.to_thread(_query)
        return _from_firestore_dict(OnboardingJourney, data) if data else None

    async def create(self, journey: OnboardingJourney) -> OnboardingJourney:
        await asyncio.to_thread(self.col.document(journey.id).set, _to_firestore_dict(journey))
        return journey

    async def update(self, journey: OnboardingJourney) -> OnboardingJourney:
        await asyncio.to_thread(self.col.document(journey.id).set, _to_firestore_dict(journey), merge=True)
        return journey


class FirestoreBrandComplianceRepository(BrandComplianceRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("brand_compliance_reports")

    async def get(self, report_id: str) -> Optional[BrandComplianceReport]:
        doc = await asyncio.to_thread(self.col.document(report_id).get)
        return _from_firestore_dict(BrandComplianceReport, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, status: Optional[str] = None) -> tuple[list[BrandComplianceReport], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(BrandComplianceReport, d.to_dict()) for d in docs]
            if status:
                items = [b for b in items if getattr(b.status, "value", str(b.status)) == status]
            items.sort(key=lambda b: b.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, report: BrandComplianceReport) -> BrandComplianceReport:
        await asyncio.to_thread(self.col.document(report.id).set, _to_firestore_dict(report))
        return report


class FirestoreActionExecutionRepository(ActionExecutionRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("action_execution_records")

    async def get(self, action_id: str) -> Optional[ActionExecutionRecord]:
        doc = await asyncio.to_thread(self.col.document(action_id).get)
        return _from_firestore_dict(ActionExecutionRecord, doc.to_dict()) if doc.exists else None

    async def list(self, skip: int = 0, limit: int = 20, action_type: Optional[str] = None) -> tuple[list[ActionExecutionRecord], int]:
        def _query():
            docs = list(self.col.stream())
            items = [_from_firestore_dict(ActionExecutionRecord, d.to_dict()) for d in docs]
            if action_type:
                items = [a for a in items if a.action_type == action_type]
            items.sort(key=lambda a: a.created_at, reverse=True)
            return items[skip:skip + limit], len(items)
        return await asyncio.to_thread(_query)

    async def create(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        await asyncio.to_thread(self.col.document(record.id).set, _to_firestore_dict(record))
        return record

    async def update(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        await asyncio.to_thread(self.col.document(record.id).set, _to_firestore_dict(record), merge=True)
        return record


class FirestoreGuidelineVersionRepository(GuidelineVersionRepository):
    def __init__(self, client=None):
        self.client = client or get_firestore_client()
        self.col = self.client.collection("guideline_version_records")

    async def get(self, record_id: str) -> Optional[GuidelineVersionRecord]:
        doc = await asyncio.to_thread(self.col.document(record_id).get)
        return _from_firestore_dict(GuidelineVersionRecord, doc.to_dict()) if doc.exists else None

    async def list_by_guideline(self, guideline_id: str) -> list[GuidelineVersionRecord]:
        def _query():
            docs = list(self.col.where("guideline_id", "==", guideline_id).stream())
            items = [_from_firestore_dict(GuidelineVersionRecord, d.to_dict()) for d in docs]
            items.sort(key=lambda g: g.created_at, reverse=True)
            return items
        return await asyncio.to_thread(_query)

    async def create(self, record: GuidelineVersionRecord) -> GuidelineVersionRecord:
        await asyncio.to_thread(self.col.document(record.id).set, _to_firestore_dict(record))
        return record
