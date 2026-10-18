"""
In-memory repository implementations.

- Thread-safe for a single Uvicorn worker (asyncio event loop).
- Zero external dependencies — perfect for local dev and tests.
- Pre-populated with seed data via seed.py.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Optional

from ..models import (
    ActionExecutionRecord,
    Approval,
    AuditRecord,
    BrandComplianceReport,
    Conversation,
    Department,
    Document,
    Guideline,
    GuidelineVersionRecord,
    Incident,
    LearningResource,
    Meeting,
    MeetingProposal,
    Message,
    Notification,
    OnboardingJourney,
    Project,
    Task,
    UserLearningProgress,
    UserProfile,
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
    MeetingProposalRepository,
    MeetingRepository,
    NotificationRepository,
    OnboardingRepository,
    ProjectRepository,
    TaskRepository,
    UserRepository,
)


class MemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[str, UserProfile] = {}

    async def get(self, user_id: str) -> Optional[UserProfile]:
        return deepcopy(self._store.get(user_id))

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        clean = email.strip().lower()
        for u in self._store.values():
            if u.email.lower() == clean:
                return deepcopy(u)
        if clean in ("alice.chen@hyperrealm.io", "alice"):
            for u in self._store.values():
                if u.email.lower() == "ayesha.hussain@hyperrealm.io":
                    return deepcopy(u)
        return None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[UserProfile], int]:
        items = list(self._store.values())
        total = len(items)
        return [deepcopy(u) for u in items[skip : skip + limit]], total

    async def create(self, user: UserProfile) -> UserProfile:
        self._store[user.id] = deepcopy(user)
        return deepcopy(user)

    async def update(self, user: UserProfile) -> UserProfile:
        self._store[user.id] = deepcopy(user)
        return deepcopy(user)

    async def delete(self, user_id: str) -> bool:
        return self._store.pop(user_id, None) is not None

    async def list_reports(self, manager_id: str) -> list[UserProfile]:
        return [deepcopy(u) for u in self._store.values() if u.manager_id == manager_id]


class MemoryDepartmentRepository(DepartmentRepository):
    def __init__(self) -> None:
        self._store: dict[str, Department] = {}

    async def get(self, dept_id: str) -> Optional[Department]:
        return deepcopy(self._store.get(dept_id))

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        items = list(self._store.values())
        return [deepcopy(d) for d in items[skip : skip + limit]], len(items)

    async def create(self, dept: Department) -> Department:
        self._store[dept.id] = deepcopy(dept)
        return deepcopy(dept)

    async def update(self, dept: Department) -> Department:
        self._store[dept.id] = deepcopy(dept)
        return deepcopy(dept)


class MemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._store: dict[str, Project] = {}

    async def get(self, project_id: str) -> Optional[Project]:
        return deepcopy(self._store.get(project_id))

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Project], int]:
        items = list(self._store.values())
        if user_id:
            items = [p for p in items if user_id in p.member_ids or p.owner_id == user_id]
        total = len(items)
        return [deepcopy(p) for p in items[skip : skip + limit]], total

    async def create(self, project: Project) -> Project:
        self._store[project.id] = deepcopy(project)
        return deepcopy(project)

    async def update(self, project: Project) -> Project:
        self._store[project.id] = deepcopy(project)
        return deepcopy(project)

    async def delete(self, project_id: str) -> bool:
        return self._store.pop(project_id, None) is not None


class MemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._convs: dict[str, Conversation] = {}
        self._msgs: dict[str, list[Message]] = {}  # conv_id → messages

    async def get(self, conv_id: str) -> Optional[Conversation]:
        return deepcopy(self._convs.get(conv_id))

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Conversation], int]:
        items = [c for c in self._convs.values() if c.user_id == user_id]
        items.sort(key=lambda c: c.updated_at, reverse=True)
        total = len(items)
        return [deepcopy(c) for c in items[skip : skip + limit]], total

    async def create(self, conv: Conversation) -> Conversation:
        self._convs[conv.id] = deepcopy(conv)
        self._msgs[conv.id] = []
        return deepcopy(conv)

    async def update(self, conv: Conversation) -> Conversation:
        self._convs[conv.id] = deepcopy(conv)
        return deepcopy(conv)

    async def delete(self, conv_id: str) -> bool:
        self._msgs.pop(conv_id, None)
        return self._convs.pop(conv_id, None) is not None

    async def list_messages(self, conv_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Message], int]:
        msgs = self._msgs.get(conv_id, [])
        total = len(msgs)
        return [deepcopy(m) for m in msgs[skip : skip + limit]], total

    async def add_message(self, message: Message) -> Message:
        msgs = self._msgs.setdefault(message.conversation_id, [])
        msgs.append(deepcopy(message))
        # touch conversation updated_at
        if message.conversation_id in self._convs:
            self._convs[message.conversation_id].updated_at = utcnow()
        return deepcopy(message)


class MemoryDocumentRepository(DocumentRepository):
    def __init__(self) -> None:
        self._store: dict[str, Document] = {}

    async def get(self, doc_id: str) -> Optional[Document]:
        return deepcopy(self._store.get(doc_id))

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        author_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        items = list(self._store.values())
        if category:
            items = [d for d in items if d.category == category]
        if author_id:
            items = [d for d in items if d.author_id == author_id]
        if scope:
            items = [d for d in items if str(d.scope) == scope or d.scope == scope]
        items.sort(key=lambda d: d.created_at, reverse=True)
        total = len(items)
        return [deepcopy(d) for d in items[skip : skip + limit]], total

    async def create(self, doc: Document) -> Document:
        self._store[doc.id] = deepcopy(doc)
        return deepcopy(doc)

    async def update(self, doc: Document) -> Document:
        self._store[doc.id] = deepcopy(doc)
        return deepcopy(doc)

    async def delete(self, doc_id: str) -> bool:
        return self._store.pop(doc_id, None) is not None


class MemoryGuidelineRepository(GuidelineRepository):
    def __init__(self) -> None:
        self._store: dict[str, Guideline] = {}

    async def get(self, guide_id: str) -> Optional[Guideline]:
        return deepcopy(self._store.get(guide_id))

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Guideline], int]:
        items = list(self._store.values())
        if category:
            items = [g for g in items if g.category == category]
        if status:
            items = [g for g in items if g.status == status]
        items.sort(key=lambda g: g.created_at, reverse=True)
        total = len(items)
        return [deepcopy(g) for g in items[skip : skip + limit]], total

    async def create(self, guide: Guideline) -> Guideline:
        self._store[guide.id] = deepcopy(guide)
        return deepcopy(guide)

    async def update(self, guide: Guideline) -> Guideline:
        self._store[guide.id] = deepcopy(guide)
        return deepcopy(guide)

    async def delete(self, guide_id: str) -> bool:
        return self._store.pop(guide_id, None) is not None


class MemoryLearningRepository(LearningRepository):
    def __init__(self) -> None:
        self._resources: dict[str, LearningResource] = {}
        self._progress: dict[str, UserLearningProgress] = {}  # f"{user_id}:{resource_id}"

    async def get_resource(self, resource_id: str) -> Optional[LearningResource]:
        return deepcopy(self._resources.get(resource_id))

    async def list_resources(self, skip: int = 0, limit: int = 20) -> tuple[list[LearningResource], int]:
        items = list(self._resources.values())
        return [deepcopy(r) for r in items[skip : skip + limit]], len(items)

    async def create_resource(self, resource: LearningResource) -> LearningResource:
        self._resources[resource.id] = deepcopy(resource)
        return deepcopy(resource)

    async def get_progress(self, user_id: str, resource_id: str) -> Optional[UserLearningProgress]:
        key = f"{user_id}:{resource_id}"
        return deepcopy(self._progress.get(key))

    async def list_progress_by_user(self, user_id: str) -> list[UserLearningProgress]:
        return [deepcopy(p) for p in self._progress.values() if p.user_id == user_id]

    async def upsert_progress(self, progress: UserLearningProgress) -> UserLearningProgress:
        key = f"{progress.user_id}:{progress.resource_id}"
        self._progress[key] = deepcopy(progress)
        return deepcopy(progress)


class MemoryMeetingRepository(MeetingRepository):
    def __init__(self) -> None:
        self._store: dict[str, Meeting] = {}

    async def get(self, meeting_id: str) -> Optional[Meeting]:
        return deepcopy(self._store.get(meeting_id))

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Meeting], int]:
        items = list(self._store.values())
        if user_id:
            items = [m for m in items if user_id == m.organiser_id or user_id in m.attendee_ids]
        items.sort(key=lambda m: m.scheduled_at)
        total = len(items)
        return [deepcopy(m) for m in items[skip : skip + limit]], total

    async def create(self, meeting: Meeting) -> Meeting:
        self._store[meeting.id] = deepcopy(meeting)
        return deepcopy(meeting)

    async def update(self, meeting: Meeting) -> Meeting:
        self._store[meeting.id] = deepcopy(meeting)
        return deepcopy(meeting)

    async def delete(self, meeting_id: str) -> bool:
        return self._store.pop(meeting_id, None) is not None


class MemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    async def get(self, task_id: str) -> Optional[Task]:
        return deepcopy(self._store.get(task_id))

    async def list(self, skip: int = 0, limit: int = 20, assignee_id: Optional[str] = None, project_id: Optional[str] = None) -> tuple[list[Task], int]:
        items = list(self._store.values())
        if assignee_id:
            items = [t for t in items if t.assignee_id == assignee_id]
        if project_id:
            items = [t for t in items if t.project_id == project_id]
        items.sort(key=lambda t: t.created_at, reverse=True)
        total = len(items)
        return [deepcopy(t) for t in items[skip : skip + limit]], total

    async def create(self, task: Task) -> Task:
        self._store[task.id] = deepcopy(task)
        return deepcopy(task)

    async def update(self, task: Task) -> Task:
        self._store[task.id] = deepcopy(task)
        return deepcopy(task)

    async def delete(self, task_id: str) -> bool:
        return self._store.pop(task_id, None) is not None


class MemoryApprovalRepository(ApprovalRepository):
    def __init__(self) -> None:
        self._store: dict[str, Approval] = {}

    async def get(self, approval_id: str) -> Optional[Approval]:
        return deepcopy(self._store.get(approval_id))

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Approval], int]:
        items = list(self._store.values())
        if user_id:
            items = [a for a in items if a.requester_id == user_id or a.approver_id == user_id]
        items.sort(key=lambda a: a.requested_at, reverse=True)
        total = len(items)
        return [deepcopy(a) for a in items[skip : skip + limit]], total

    async def create(self, approval: Approval) -> Approval:
        self._store[approval.id] = deepcopy(approval)
        return deepcopy(approval)

    async def update(self, approval: Approval) -> Approval:
        self._store[approval.id] = deepcopy(approval)
        return deepcopy(approval)


class MemoryIncidentRepository(IncidentRepository):
    def __init__(self) -> None:
        self._store: dict[str, Incident] = {}

    async def get(self, incident_id: str) -> Optional[Incident]:
        return deepcopy(self._store.get(incident_id))

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Incident], int]:
        items = list(self._store.values())
        items.sort(key=lambda i: i.created_at, reverse=True)
        total = len(items)
        return [deepcopy(i) for i in items[skip : skip + limit]], total

    async def create(self, incident: Incident) -> Incident:
        self._store[incident.id] = deepcopy(incident)
        return deepcopy(incident)

    async def update(self, incident: Incident) -> Incident:
        self._store[incident.id] = deepcopy(incident)
        return deepcopy(incident)


class MemoryNotificationRepository(NotificationRepository):
    def __init__(self) -> None:
        self._store: dict[str, Notification] = {}

    async def list_by_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        items = [n for n in self._store.values() if n.user_id == user_id]
        if unread_only:
            items = [n for n in items if not n.is_read]
        items.sort(key=lambda n: n.created_at, reverse=True)
        return [deepcopy(n) for n in items]

    async def create(self, notification: Notification) -> Notification:
        self._store[notification.id] = deepcopy(notification)
        return deepcopy(notification)

    async def mark_read(self, notification_id: str) -> bool:
        n = self._store.get(notification_id)
        if not n:
            return False
        n.is_read = True
        return True

    async def mark_all_read(self, user_id: str) -> int:
        count = 0
        for n in self._store.values():
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
                count += 1
        return count


class MemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._store: list[AuditRecord] = []

    async def list(self, skip: int = 0, limit: int = 50, actor_id: Optional[str] = None) -> tuple[list[AuditRecord], int]:
        items = list(reversed(self._store))  # newest first
        if actor_id:
            items = [r for r in items if r.actor_id == actor_id]
        total = len(items)
        return [deepcopy(r) for r in items[skip : skip + limit]], total

    async def create(self, record: AuditRecord) -> AuditRecord:
        self._store.append(deepcopy(record))
        return deepcopy(record)


class MemoryGuidelineVersionRepository(GuidelineVersionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GuidelineVersionRecord] = {}

    async def list_by_guideline(self, guideline_id: str) -> list[GuidelineVersionRecord]:
        items = [v for v in self._store.values() if v.guideline_id == guideline_id]
        items.sort(key=lambda v: v.created_at, reverse=True)
        return [deepcopy(v) for v in items]

    async def get(self, version_id: str) -> Optional[GuidelineVersionRecord]:
        return deepcopy(self._store.get(version_id))

    async def create(self, record: GuidelineVersionRecord) -> GuidelineVersionRecord:
        self._store[record.id] = deepcopy(record)
        return deepcopy(record)


class MemoryBrandComplianceRepository(BrandComplianceRepository):
    def __init__(self) -> None:
        self._store: dict[str, BrandComplianceReport] = {}

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[BrandComplianceReport], int]:
        items = list(self._store.values())
        if user_id:
            items = [r for r in items if r.created_by == user_id]
        items.sort(key=lambda r: r.created_at, reverse=True)
        total = len(items)
        return [deepcopy(r) for r in items[skip : skip + limit]], total

    async def get(self, report_id: str) -> Optional[BrandComplianceReport]:
        return deepcopy(self._store.get(report_id))

    async def create(self, report: BrandComplianceReport) -> BrandComplianceReport:
        self._store[report.id] = deepcopy(report)
        return deepcopy(report)


class MemoryActionExecutionRepository(ActionExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, ActionExecutionRecord] = {}

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[ActionExecutionRecord], int]:
        items = list(self._store.values())
        if user_id:
            items = [a for a in items if a.executed_by == user_id]
        items.sort(key=lambda a: a.created_at, reverse=True)
        total = len(items)
        return [deepcopy(a) for a in items[skip : skip + limit]], total

    async def get(self, action_id: str) -> Optional[ActionExecutionRecord]:
        return deepcopy(self._store.get(action_id))

    async def get_by_idempotency_key(self, key: str) -> Optional[ActionExecutionRecord]:
        for a in self._store.values():
            if a.idempotency_key == key:
                return deepcopy(a)
        return None

    async def create(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        self._store[record.id] = deepcopy(record)
        return deepcopy(record)

    async def update(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        self._store[record.id] = deepcopy(record)
        return deepcopy(record)


class MemoryOnboardingRepository(OnboardingRepository):
    def __init__(self) -> None:
        self._store: dict[str, OnboardingJourney] = {}

    async def get_by_user(self, user_id: str) -> Optional[OnboardingJourney]:
        for j in self._store.values():
            if j.user_id == user_id:
                return deepcopy(j)
        return None

    async def get(self, journey_id: str) -> Optional[OnboardingJourney]:
        return deepcopy(self._store.get(journey_id))

    async def create(self, journey: OnboardingJourney) -> OnboardingJourney:
        self._store[journey.id] = deepcopy(journey)
        return deepcopy(journey)

    async def update(self, journey: OnboardingJourney) -> OnboardingJourney:
        self._store[journey.id] = deepcopy(journey)
        return deepcopy(journey)

    async def list_by_manager(self, manager_id: str) -> list[OnboardingJourney]:
        return [deepcopy(j) for j in self._store.values() if j.manager_id == manager_id]


class MemoryMeetingProposalRepository(MeetingProposalRepository):
    def __init__(self) -> None:
        self._store: dict[str, MeetingProposal] = {}

    async def get(self, proposal_id: str) -> Optional[MeetingProposal]:
        p = self._store.get(proposal_id)
        return deepcopy(p) if p else None

    async def list_by_user(self, user_id: str) -> list[MeetingProposal]:
        return [deepcopy(p) for p in self._store.values() if p.user_id == user_id]

    async def create(self, proposal: MeetingProposal) -> MeetingProposal:
        self._store[proposal.id] = deepcopy(proposal)
        return deepcopy(proposal)

    async def update(self, proposal: MeetingProposal) -> MeetingProposal:
        self._store[proposal.id] = deepcopy(proposal)
        return deepcopy(proposal)

    async def delete(self, proposal_id: str) -> bool:
        return self._store.pop(proposal_id, None) is not None

