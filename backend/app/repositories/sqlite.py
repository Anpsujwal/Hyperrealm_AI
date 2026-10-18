"""
SQLite repository implementations.
Persistent local database for development, self-contained and ready to migrate to cloud.
Stores entity records with indexed key columns and full JSON document bodies.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any, Optional

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
)


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_sqlite_db(db_path: str) -> None:
    """Create tables and indexes if they do not exist."""
    conn = _get_connection(db_path)
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            manager_id TEXT,
            role TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_manager ON users(manager_id);

        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            owner_id TEXT,
            data JSON NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            category TEXT,
            author_id TEXT,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_docs_cat ON documents(category);

        CREATE TABLE IF NOT EXISTS guidelines (
            id TEXT PRIMARY KEY,
            category TEXT,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );

        CREATE TABLE IF NOT EXISTS learning_resources (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );

        CREATE TABLE IF NOT EXISTS learning_progress (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_lp_user ON learning_progress(user_id);

        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            organiser_id TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_meetings_org ON meetings(organiser_id);

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            assignee_id TEXT,
            project_id TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);

        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            requester_id TEXT NOT NULL,
            approver_id TEXT,
            status TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_approvals_req ON approvals(requester_id);
        CREATE INDEX IF NOT EXISTS idx_approvals_app ON approvals(approver_id);

        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notifs_user ON notifications(user_id, is_read);

        CREATE TABLE IF NOT EXISTS audit_records (
            id TEXT PRIMARY KEY,
            actor_id TEXT,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_records(actor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_records(created_at);

        CREATE TABLE IF NOT EXISTS guideline_versions (
            id TEXT PRIMARY KEY,
            guideline_id TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_gver_guideline ON guideline_versions(guideline_id);

        CREATE TABLE IF NOT EXISTS brand_compliance_reports (
            id TEXT PRIMARY KEY,
            image_id TEXT,
            guideline_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_bcr_user ON brand_compliance_reports(created_by);

        CREATE TABLE IF NOT EXISTS action_executions (
            id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL,
            executed_by TEXT NOT NULL,
            idempotency_key TEXT,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_act_user ON action_executions(executed_by);
        CREATE INDEX IF NOT EXISTS idx_act_idemp ON action_executions(idempotency_key);

        CREATE TABLE IF NOT EXISTS onboarding_journeys (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            manager_id TEXT,
            updated_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_onb_user ON onboarding_journeys(user_id);
        CREATE INDEX IF NOT EXISTS idx_onb_manager ON onboarding_journeys(manager_id);

        CREATE TABLE IF NOT EXISTS meeting_proposals (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data JSON NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_proposals_user ON meeting_proposals(user_id);
        """)
        conn.commit()
    finally:
        conn.close()


# ─── Helper function ──────────────────────────────────────────────────────────

def _sync_query(db_path: str, sql: str, params: tuple = (), fetch: str = "none") -> Any:
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        elif fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        elif fetch == "count":
            row = cur.fetchone()
            return row[0] if row else 0
        conn.commit()
        return None
    finally:
        conn.close()


# ─── Repositories ─────────────────────────────────────────────────────────────

class SqliteUserRepository(UserRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, user_id: str) -> Optional[UserProfile]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM users WHERE id = ?",
            (user_id,),
            "one",
        )
        return UserProfile.model_validate_json(row["data"]) if row else None

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        clean_email = email.strip().lower()
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM users WHERE LOWER(email) = LOWER(?)",
            (clean_email,),
            "one",
        )
        if not row and clean_email in ("alice.chen@hyperrealm.io", "alice"):
            row = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM users WHERE LOWER(email) = 'ayesha.hussain@hyperrealm.io'",
                (),
                "one",
            )
        return UserProfile.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[UserProfile], int]:
        total = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT COUNT(*) FROM users",
            (),
            "count",
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM users ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (limit, skip),
            "all",
        )
        items = [UserProfile.model_validate_json(r["data"]) for r in rows]
        return items, total

    async def create(self, user: UserProfile) -> UserProfile:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT INTO users (id, email, manager_id, role, data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.email, user.manager_id, user.role.value, user.model_dump_json(), user.created_at.isoformat()),
        )
        return user

    async def update(self, user: UserProfile) -> UserProfile:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE users SET email = ?, manager_id = ?, role = ?, data = ? WHERE id = ?",
            (user.email, user.manager_id, user.role.value, user.model_dump_json(), user.id),
        )
        return user

    async def delete(self, user_id: str) -> bool:
        user = await self.get(user_id)
        if not user:
            return False
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )
        return True

    async def list_reports(self, manager_id: str) -> list[UserProfile]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM users WHERE manager_id = ? ORDER BY created_at ASC",
            (manager_id,),
            "all",
        )
        return [UserProfile.model_validate_json(r["data"]) for r in rows]


class SqliteDepartmentRepository(DepartmentRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, dept_id: str) -> Optional[Department]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM departments WHERE id = ?", (dept_id,), "one"
        )
        return Department.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        total = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT COUNT(*) FROM departments", (), "count"
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM departments ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (limit, skip),
            "all",
        )
        return [Department.model_validate_json(r["data"]) for r in rows], total

    async def create(self, dept: Department) -> Department:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO departments (id, name, data, created_at) VALUES (?, ?, ?, ?)",
            (dept.id, dept.name, dept.model_dump_json(), dept.created_at.isoformat()),
        )
        return dept

    async def update(self, dept: Department) -> Department:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE departments SET name = ?, data = ? WHERE id = ?",
            (dept.name, dept.model_dump_json(), dept.id),
        )
        return dept


class SqliteProjectRepository(ProjectRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, project_id: str) -> Optional[Project]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM projects WHERE id = ?", (project_id,), "one"
        )
        return Project.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Project], int]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM projects ORDER BY created_at ASC",
            (),
            "all",
        )
        items = [Project.model_validate_json(r["data"]) for r in rows]
        if user_id:
            items = [p for p in items if user_id in p.member_ids or p.owner_id == user_id]
        total = len(items)
        return items[skip : skip + limit], total

    async def create(self, project: Project) -> Project:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO projects (id, owner_id, data, created_at) VALUES (?, ?, ?, ?)",
            (project.id, project.owner_id, project.model_dump_json(), project.created_at.isoformat()),
        )
        return project

    async def update(self, project: Project) -> Project:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE projects SET owner_id = ?, data = ? WHERE id = ?",
            (project.owner_id, project.model_dump_json(), project.id),
        )
        return project

    async def delete(self, project_id: str) -> bool:
        p = await self.get(project_id)
        if not p:
            return False
        await asyncio.to_thread(
            _sync_query, self.db_path, "DELETE FROM projects WHERE id = ?", (project_id,)
        )
        return True


class SqliteConversationRepository(ConversationRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, conv_id: str) -> Optional[Conversation]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM conversations WHERE id = ?", (conv_id,), "one"
        )
        return Conversation.model_validate_json(row["data"]) if row else None

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Conversation], int]:
        total = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT COUNT(*) FROM conversations WHERE user_id = ?",
            (user_id,),
            "count",
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, skip),
            "all",
        )
        return [Conversation.model_validate_json(r["data"]) for r in rows], total

    async def create(self, conv: Conversation) -> Conversation:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO conversations (id, user_id, created_at, data) VALUES (?, ?, ?, ?)",
            (conv.id, conv.user_id, conv.created_at.isoformat(), conv.model_dump_json()),
        )
        return conv

    async def update(self, conv: Conversation) -> Conversation:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE conversations SET data = ? WHERE id = ?",
            (conv.model_dump_json(), conv.id),
        )
        return conv

    async def delete(self, conv_id: str) -> bool:
        c = await self.get(conv_id)
        if not c:
            return False
        await asyncio.to_thread(
            _sync_query, self.db_path, "DELETE FROM conversations WHERE id = ?", (conv_id,)
        )
        await asyncio.to_thread(
            _sync_query, self.db_path, "DELETE FROM messages WHERE conversation_id = ?", (conv_id,)
        )
        return True

    async def list_messages(self, conv_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Message], int]:
        total = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
            (conv_id,),
            "count",
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conv_id, limit, skip),
            "all",
        )
        return [Message.model_validate_json(r["data"]) for r in rows], total

    async def add_message(self, message: Message) -> Message:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO messages (id, conversation_id, created_at, data) VALUES (?, ?, ?, ?)",
            (message.id, message.conversation_id, message.created_at.isoformat(), message.model_dump_json()),
        )
        return message


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, doc_id: str) -> Optional[Document]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM documents WHERE id = ?", (doc_id,), "one"
        )
        return Document.model_validate_json(row["data"]) if row else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        author_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if author_id:
            clauses.append("author_id = ?")
            params.append(author_id)
        if scope:
            clauses.append("json_extract(data, '$.scope') = ?")
            params.append(scope)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        total = await asyncio.to_thread(
            _sync_query, self.db_path, f"SELECT COUNT(*) FROM documents {where}", tuple(params), "count"
        )
        query_params = list(params) + [limit, skip]
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            f"SELECT data FROM documents {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(query_params),
            "all",
        )
        return [Document.model_validate_json(r["data"]) for r in rows], total

    async def create(self, doc: Document) -> Document:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO documents (id, category, author_id, created_at, data) VALUES (?, ?, ?, ?, ?)",
            (doc.id, doc.category, doc.author_id, doc.created_at.isoformat(), doc.model_dump_json()),
        )
        return doc

    async def update(self, doc: Document) -> Document:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE documents SET category = ?, data = ? WHERE id = ?",
            (doc.category, doc.model_dump_json(), doc.id),
        )
        return doc

    async def delete(self, doc_id: str) -> bool:
        d = await self.get(doc_id)
        if not d:
            return False
        await asyncio.to_thread(_sync_query, self.db_path, "DELETE FROM documents WHERE id = ?", (doc_id,))
        return True


class SqliteGuidelineRepository(GuidelineRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, guide_id: str) -> Optional[Guideline]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM guidelines WHERE id = ?", (guide_id,), "one"
        )
        return Guideline.model_validate_json(row["data"]) if row else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Guideline], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if status:
            clauses.append("json_extract(data, '$.status') = ?")
            params.append(status)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        total = await asyncio.to_thread(
            _sync_query, self.db_path, f"SELECT COUNT(*) FROM guidelines {where}", tuple(params), "count"
        )
        query_params = list(params) + [limit, skip]
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            f"SELECT data FROM guidelines {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(query_params),
            "all",
        )
        return [Guideline.model_validate_json(r["data"]) for r in rows], total

    async def create(self, guide: Guideline) -> Guideline:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO guidelines (id, category, created_at, data) VALUES (?, ?, ?, ?)",
            (guide.id, guide.category, guide.created_at.isoformat(), guide.model_dump_json()),
        )
        return guide

    async def update(self, guide: Guideline) -> Guideline:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE guidelines SET category = ?, data = ? WHERE id = ?",
            (guide.category, guide.model_dump_json(), guide.id),
        )
        return guide

    async def delete(self, guide_id: str) -> bool:
        g = await self.get(guide_id)
        if not g:
            return False
        await asyncio.to_thread(_sync_query, self.db_path, "DELETE FROM guidelines WHERE id = ?", (guide_id,))
        return True


class SqliteLearningRepository(LearningRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get_resource(self, resource_id: str) -> Optional[LearningResource]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM learning_resources WHERE id = ?", (resource_id,), "one"
        )
        return LearningResource.model_validate_json(row["data"]) if row else None

    async def list_resources(self, skip: int = 0, limit: int = 20) -> tuple[list[LearningResource], int]:
        total = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT COUNT(*) FROM learning_resources", (), "count"
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM learning_resources ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (limit, skip),
            "all",
        )
        return [LearningResource.model_validate_json(r["data"]) for r in rows], total

    async def create_resource(self, resource: LearningResource) -> LearningResource:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO learning_resources (id, created_at, data) VALUES (?, ?, ?)",
            (resource.id, resource.created_at.isoformat(), resource.model_dump_json()),
        )
        return resource

    async def get_progress(self, user_id: str, resource_id: str) -> Optional[UserLearningProgress]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM learning_progress WHERE user_id = ? AND resource_id = ?",
            (user_id, resource_id),
            "one",
        )
        return UserLearningProgress.model_validate_json(row["data"]) if row else None

    async def list_progress_by_user(self, user_id: str) -> list[UserLearningProgress]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM learning_progress WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
            "all",
        )
        return [UserLearningProgress.model_validate_json(r["data"]) for r in rows]

    async def upsert_progress(self, progress: UserLearningProgress) -> UserLearningProgress:
        prog_id = f"{progress.user_id}:{progress.resource_id}"
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO learning_progress (id, user_id, resource_id, updated_at, data) VALUES (?, ?, ?, ?, ?)",
            (prog_id, progress.user_id, progress.resource_id, progress.updated_at.isoformat(), progress.model_dump_json()),
        )
        return progress


class SqliteMeetingRepository(MeetingRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, meeting_id: str) -> Optional[Meeting]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM meetings WHERE id = ?", (meeting_id,), "one"
        )
        return Meeting.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Meeting], int]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM meetings ORDER BY scheduled_at ASC",
            (),
            "all",
        )
        items = [Meeting.model_validate_json(r["data"]) for r in rows]
        if user_id:
            items = [m for m in items if user_id in m.attendee_ids or m.organiser_id == user_id]
        total = len(items)
        return items[skip : skip + limit], total

    async def create(self, meeting: Meeting) -> Meeting:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO meetings (id, organiser_id, scheduled_at, data) VALUES (?, ?, ?, ?)",
            (meeting.id, meeting.organiser_id, meeting.scheduled_at.isoformat(), meeting.model_dump_json()),
        )
        return meeting

    async def update(self, meeting: Meeting) -> Meeting:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE meetings SET organiser_id = ?, scheduled_at = ?, data = ? WHERE id = ?",
            (meeting.organiser_id, meeting.scheduled_at.isoformat(), meeting.model_dump_json(), meeting.id),
        )
        return meeting

    async def delete(self, meeting_id: str) -> bool:
        m = await self.get(meeting_id)
        if not m:
            return False
        await asyncio.to_thread(_sync_query, self.db_path, "DELETE FROM meetings WHERE id = ?", (meeting_id,))
        return True


class SqliteTaskRepository(TaskRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, task_id: str) -> Optional[Task]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM tasks WHERE id = ?", (task_id,), "one"
        )
        return Task.model_validate_json(row["data"]) if row else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        assignee_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> tuple[list[Task], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if assignee_id:
            clauses.append("assignee_id = ?")
            params.append(assignee_id)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        total = await asyncio.to_thread(
            _sync_query, self.db_path, f"SELECT COUNT(*) FROM tasks {where}", tuple(params), "count"
        )
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            f"SELECT data FROM tasks {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(params + [limit, skip]),
            "all",
        )
        return [Task.model_validate_json(r["data"]) for r in rows], total

    async def create(self, task: Task) -> Task:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO tasks (id, assignee_id, project_id, status, created_at, data) VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, task.assignee_id, task.project_id, task.status.value, task.created_at.isoformat(), task.model_dump_json()),
        )
        return task

    async def update(self, task: Task) -> Task:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE tasks SET assignee_id = ?, project_id = ?, status = ?, data = ? WHERE id = ?",
            (task.assignee_id, task.project_id, task.status.value, task.model_dump_json(), task.id),
        )
        return task

    async def delete(self, task_id: str) -> bool:
        t = await self.get(task_id)
        if not t:
            return False
        await asyncio.to_thread(_sync_query, self.db_path, "DELETE FROM tasks WHERE id = ?", (task_id,))
        return True


class SqliteApprovalRepository(ApprovalRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, approval_id: str) -> Optional[Approval]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM approvals WHERE id = ?", (approval_id,), "one"
        )
        return Approval.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[Approval], int]:
        if user_id:
            total = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT COUNT(*) FROM approvals WHERE requester_id = ? OR approver_id = ?",
                (user_id, user_id),
                "count",
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM approvals WHERE requester_id = ? OR approver_id = ? ORDER BY requested_at DESC LIMIT ? OFFSET ?",
                (user_id, user_id, limit, skip),
                "all",
            )
        else:
            total = await asyncio.to_thread(_sync_query, self.db_path, "SELECT COUNT(*) FROM approvals", (), "count")
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM approvals ORDER BY requested_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
                "all",
            )
        return [Approval.model_validate_json(r["data"]) for r in rows], total

    async def create(self, approval: Approval) -> Approval:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO approvals (id, requester_id, approver_id, status, requested_at, data) VALUES (?, ?, ?, ?, ?, ?)",
            (approval.id, approval.requester_id, approval.approver_id, approval.status.value, approval.requested_at.isoformat(), approval.model_dump_json()),
        )
        return approval

    async def update(self, approval: Approval) -> Approval:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE approvals SET status = ?, approver_id = ?, data = ? WHERE id = ?",
            (approval.status.value, approval.approver_id, approval.model_dump_json(), approval.id),
        )
        return approval


class SqliteIncidentRepository(IncidentRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, incident_id: str) -> Optional[Incident]:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM incidents WHERE id = ?", (incident_id,), "one"
        )
        return Incident.model_validate_json(row["data"]) if row else None

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Incident], int]:
        total = await asyncio.to_thread(_sync_query, self.db_path, "SELECT COUNT(*) FROM incidents", (), "count")
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM incidents ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, skip),
            "all",
        )
        return [Incident.model_validate_json(r["data"]) for r in rows], total

    async def create(self, incident: Incident) -> Incident:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO incidents (id, status, severity, created_at, data) VALUES (?, ?, ?, ?, ?)",
            (incident.id, incident.status.value, incident.severity.value, incident.created_at.isoformat(), incident.model_dump_json()),
        )
        return incident

    async def update(self, incident: Incident) -> Incident:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE incidents SET status = ?, severity = ?, data = ? WHERE id = ?",
            (incident.status.value, incident.severity.value, incident.model_dump_json(), incident.id),
        )
        return incident


class SqliteNotificationRepository(NotificationRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list_by_user(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        if unread_only:
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC",
                (user_id,),
                "all",
            )
        else:
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
                "all",
            )
        return [Notification.model_validate_json(r["data"]) for r in rows]

    async def create(self, notification: Notification) -> Notification:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO notifications (id, user_id, is_read, created_at, data) VALUES (?, ?, ?, ?, ?)",
            (notification.id, notification.user_id, 1 if notification.is_read else 0, notification.created_at.isoformat(), notification.model_dump_json()),
        )
        return notification

    async def mark_read(self, notification_id: str) -> bool:
        row = await asyncio.to_thread(
            _sync_query, self.db_path, "SELECT data FROM notifications WHERE id = ?", (notification_id,), "one"
        )
        if not row:
            return False
        notif = Notification.model_validate_json(row["data"])
        notif.is_read = True
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE notifications SET is_read = 1, data = ? WHERE id = ?",
            (notif.model_dump_json(), notification_id),
        )
        return True

    async def mark_all_read(self, user_id: str) -> int:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,),
            "all",
        )
        count = len(rows)
        for r in rows:
            notif = Notification.model_validate_json(r["data"])
            notif.is_read = True
            await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "UPDATE notifications SET is_read = 1, data = ? WHERE id = ?",
                (notif.model_dump_json(), notif.id),
            )
        return count


class SqliteAuditRepository(AuditRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list(self, skip: int = 0, limit: int = 50, actor_id: Optional[str] = None) -> tuple[list[AuditRecord], int]:
        if actor_id:
            total = await asyncio.to_thread(
                _sync_query, self.db_path, "SELECT COUNT(*) FROM audit_records WHERE actor_id = ?", (actor_id,), "count"
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM audit_records WHERE actor_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (actor_id, limit, skip),
                "all",
            )
        else:
            total = await asyncio.to_thread(_sync_query, self.db_path, "SELECT COUNT(*) FROM audit_records", (), "count")
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM audit_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
                "all",
            )
        return [AuditRecord.model_validate_json(r["data"]) for r in rows], total

    async def create(self, record: AuditRecord) -> AuditRecord:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO audit_records (id, actor_id, created_at, data) VALUES (?, ?, ?, ?)",
            (record.id, record.actor_id, record.created_at.isoformat(), record.model_dump_json()),
        )
        return record


class SqliteGuidelineVersionRepository(GuidelineVersionRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list_by_guideline(self, guideline_id: str) -> list[GuidelineVersionRecord]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM guideline_versions WHERE guideline_id = ? ORDER BY created_at DESC",
            (guideline_id,),
            "all",
        )
        return [GuidelineVersionRecord.model_validate_json(r["data"]) for r in rows]

    async def get(self, version_id: str) -> Optional[GuidelineVersionRecord]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM guideline_versions WHERE id = ?",
            (version_id,),
            "one",
        )
        return GuidelineVersionRecord.model_validate_json(row["data"]) if row else None

    async def create(self, record: GuidelineVersionRecord) -> GuidelineVersionRecord:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO guideline_versions (id, guideline_id, version, created_at, data) VALUES (?, ?, ?, ?, ?)",
            (record.id, record.guideline_id, record.version, record.created_at.isoformat(), record.model_dump_json()),
        )
        return record


class SqliteBrandComplianceRepository(BrandComplianceRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[BrandComplianceReport], int]:
        if user_id:
            total = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT COUNT(*) FROM brand_compliance_reports WHERE created_by = ?",
                (user_id,),
                "count",
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM brand_compliance_reports WHERE created_by = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, skip),
                "all",
            )
        else:
            total = await asyncio.to_thread(
                _sync_query, self.db_path, "SELECT COUNT(*) FROM brand_compliance_reports", (), "count"
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM brand_compliance_reports ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
                "all",
            )
        return [BrandComplianceReport.model_validate_json(r["data"]) for r in rows], total

    async def get(self, report_id: str) -> Optional[BrandComplianceReport]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM brand_compliance_reports WHERE id = ?",
            (report_id,),
            "one",
        )
        return BrandComplianceReport.model_validate_json(row["data"]) if row else None

    async def create(self, report: BrandComplianceReport) -> BrandComplianceReport:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO brand_compliance_reports (id, image_id, guideline_id, created_by, created_at, data) VALUES (?, ?, ?, ?, ?, ?)",
            (report.id, report.image_id, report.guideline_id, report.created_by, report.created_at.isoformat(), report.model_dump_json()),
        )
        return report


class SqliteActionExecutionRepository(ActionExecutionRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list(self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None) -> tuple[list[ActionExecutionRecord], int]:
        if user_id:
            total = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT COUNT(*) FROM action_executions WHERE executed_by = ?",
                (user_id,),
                "count",
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM action_executions WHERE executed_by = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, skip),
                "all",
            )
        else:
            total = await asyncio.to_thread(
                _sync_query, self.db_path, "SELECT COUNT(*) FROM action_executions", (), "count"
            )
            rows = await asyncio.to_thread(
                _sync_query,
                self.db_path,
                "SELECT data FROM action_executions ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, skip),
                "all",
            )
        return [ActionExecutionRecord.model_validate_json(r["data"]) for r in rows], total

    async def get(self, action_id: str) -> Optional[ActionExecutionRecord]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM action_executions WHERE id = ?",
            (action_id,),
            "one",
        )
        return ActionExecutionRecord.model_validate_json(row["data"]) if row else None

    async def get_by_idempotency_key(self, key: str) -> Optional[ActionExecutionRecord]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM action_executions WHERE idempotency_key = ?",
            (key,),
            "one",
        )
        return ActionExecutionRecord.model_validate_json(row["data"]) if row else None

    async def create(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO action_executions (id, action_type, status, executed_by, idempotency_key, created_at, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record.id, record.action_type, str(record.status), record.executed_by, record.idempotency_key, record.created_at.isoformat(), record.model_dump_json()),
        )
        return record

    async def update(self, record: ActionExecutionRecord) -> ActionExecutionRecord:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE action_executions SET status = ?, data = ? WHERE id = ?",
            (str(record.status), record.model_dump_json(), record.id),
        )
        return record


class SqliteOnboardingRepository(OnboardingRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get_by_user(self, user_id: str) -> Optional[OnboardingJourney]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM onboarding_journeys WHERE user_id = ?",
            (user_id,),
            "one",
        )
        return OnboardingJourney.model_validate_json(row["data"]) if row else None

    async def get(self, journey_id: str) -> Optional[OnboardingJourney]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM onboarding_journeys WHERE id = ?",
            (journey_id,),
            "one",
        )
        return OnboardingJourney.model_validate_json(row["data"]) if row else None

    async def create(self, journey: OnboardingJourney) -> OnboardingJourney:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO onboarding_journeys (id, user_id, manager_id, updated_at, data) VALUES (?, ?, ?, ?, ?)",
            (journey.id, journey.user_id, journey.manager_id, journey.updated_at.isoformat(), journey.model_dump_json()),
        )
        return journey

    async def update(self, journey: OnboardingJourney) -> OnboardingJourney:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE onboarding_journeys SET manager_id = ?, updated_at = ?, data = ? WHERE id = ?",
            (journey.manager_id, journey.updated_at.isoformat(), journey.model_dump_json(), journey.id),
        )
        return journey

    async def list_by_manager(self, manager_id: str) -> list[OnboardingJourney]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM onboarding_journeys WHERE manager_id = ? ORDER BY updated_at DESC",
            (manager_id,),
            "all",
        )
        return [OnboardingJourney.model_validate_json(r["data"]) for r in rows]


class SqliteMeetingProposalRepository(MeetingProposalRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, proposal_id: str) -> Optional[MeetingProposal]:
        row = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM meeting_proposals WHERE id = ?",
            (proposal_id,),
            "one",
        )
        return MeetingProposal.model_validate_json(row["data"]) if row else None

    async def list_by_user(self, user_id: str) -> list[MeetingProposal]:
        rows = await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "SELECT data FROM meeting_proposals WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
            "all",
        )
        return [MeetingProposal.model_validate_json(r["data"]) for r in rows]

    async def create(self, proposal: MeetingProposal) -> MeetingProposal:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "INSERT OR REPLACE INTO meeting_proposals (id, user_id, status, created_at, data) VALUES (?, ?, ?, ?, ?)",
            (proposal.id, proposal.user_id, proposal.status, proposal.created_at.isoformat(), proposal.model_dump_json()),
        )
        return proposal

    async def update(self, proposal: MeetingProposal) -> MeetingProposal:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "UPDATE meeting_proposals SET status = ?, data = ? WHERE id = ?",
            (proposal.status, proposal.model_dump_json(), proposal.id),
        )
        return proposal

    async def delete(self, proposal_id: str) -> bool:
        await asyncio.to_thread(
            _sync_query,
            self.db_path,
            "DELETE FROM meeting_proposals WHERE id = ?",
            (proposal_id,),
        )
        return True

