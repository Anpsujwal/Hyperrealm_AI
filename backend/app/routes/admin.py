"""
Admin-only routes — audit logs, departments, projects.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..auth import AdminRequired, CurrentUser
from ..dependencies import (
    AuditRepoDep,
    DeptRepoDep,
    DocRepoDep,
    GuideRepoDep,
    LearningRepoDep,
    ProjectRepoDep,
)
from ..models import AuditAction, AuditRecord, Department, Project, UserProfile, UserRole, utcnow
from ..schemas import (
    AuditRecordOut,
    DepartmentCreate,
    DepartmentOut,
    DocumentOut,
    DocumentUpdate,
    GuidelineOut,
    GuidelineUpdate,
    LearningResourceOut,
    LearningResourceUpdate,
    PaginatedResponse,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# ─── Audit logs (admin-only) ──────────────────────────────────────────────────

@router.get("/audit", response_model=PaginatedResponse[AuditRecordOut],
            summary="Audit log (admin)")
async def list_audit_logs(
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminRequired,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    actor_id: str | None = None,
) -> PaginatedResponse[AuditRecordOut]:
    skip = (page - 1) * page_size
    records, total = await audit_repo.list(skip=skip, limit=page_size, actor_id=actor_id)
    return PaginatedResponse(
        items=[AuditRecordOut.model_validate(r.model_dump()) for r in records],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.get("/audit-logs", response_model=PaginatedResponse[AuditRecordOut],
            summary="Audit log alias (admin)")
async def list_audit_logs_alias(
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminRequired,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    actor_id: str | None = None,
) -> PaginatedResponse[AuditRecordOut]:
    return await list_audit_logs(audit_repo=audit_repo, _=_, page=page, page_size=page_size, actor_id=actor_id)


# ─── Departments ──────────────────────────────────────────────────────────────

@router.get("/departments", response_model=PaginatedResponse[DepartmentOut],
            summary="List departments")
async def list_departments(
    current_user: CurrentUser,
    dept_repo: DeptRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[DepartmentOut]:
    skip = (page - 1) * page_size
    depts, total = await dept_repo.list(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[DepartmentOut.model_validate(d.model_dump()) for d in depts],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED,
             summary="Create department (admin)")
async def create_department(
    body: DepartmentCreate,
    dept_repo: DeptRepoDep,
    audit_repo: AuditRepoDep,
    admin: UserProfile = AdminRequired,
) -> DepartmentOut:
    dept = Department(**body.model_dump())
    created = await dept_repo.create(dept)
    await audit_repo.create(AuditRecord(
        actor_id=admin.id,
        actor_email=admin.email,
        action=AuditAction.CREATE,
        resource_type="department",
        resource_id=created.id,
        description=f"Created department: {created.name}",
    ))
    return DepartmentOut.model_validate(created.model_dump())


# ─── Projects ─────────────────────────────────────────────────────────────────

@router.get("/projects", response_model=PaginatedResponse[ProjectOut], summary="List projects")
async def list_projects(
    current_user: CurrentUser,
    project_repo: ProjectRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mine: bool = False,
) -> PaginatedResponse[ProjectOut]:
    skip = (page - 1) * page_size
    projects, total = await project_repo.list(
        skip=skip, limit=page_size,
        user_id=current_user.id if mine else None,
    )
    return PaginatedResponse(
        items=[ProjectOut.model_validate(p.model_dump()) for p in projects],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED,
             summary="Create project (admin or lead)")
async def create_project(
    body: ProjectCreate,
    current_user: CurrentUser,
    project_repo: ProjectRepoDep,
    audit_repo: AuditRepoDep,
) -> ProjectOut:
    from ..auth import ROLE_HIERARCHY, UserRole
    if ROLE_HIERARCHY.get(current_user.role, 0) < ROLE_HIERARCHY[UserRole.TECHNICAL_LEAD]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Technical Lead or above required to create projects")

    project = Project(**body.model_dump())
    created = await project_repo.create(project)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="project",
        resource_id=created.id,
        description=f"Created project: {created.name}",
    ))
    return ProjectOut.model_validate(created.model_dump())


@router.get("/projects/{project_id}", response_model=ProjectOut, summary="Get project")
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    project_repo: ProjectRepoDep,
) -> ProjectOut:
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(project.model_dump())


@router.patch("/projects/{project_id}", response_model=ProjectOut, summary="Update project")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    current_user: CurrentUser,
    project_repo: ProjectRepoDep,
    audit_repo: AuditRepoDep,
) -> ProjectOut:
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    from ..models import UserRole
    if project.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the project owner or admin may update this project")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    project.updated_at = utcnow()
    updated = await project_repo.update(project)
    return ProjectOut.model_validate(updated.model_dump())


# ─── Guideline Versions & Changes (admin-only) ────────────────────────────────

@router.get("/guidelines/changes", response_model=PaginatedResponse[GuidelineOut],
            summary="List guideline versions, publication status, and affected teams (admin)")
async def list_guideline_changes(
    guide_repo: GuideRepoDep,
    _: UserProfile = AdminRequired,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[GuidelineOut]:
    skip = (page - 1) * page_size
    guides, total = await guide_repo.list(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[GuidelineOut.model_validate(g.model_dump()) for g in guides],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.patch("/guidelines/{guide_id}", response_model=GuidelineOut,
              summary="Update guideline version, status, or metadata (admin)")
async def update_guideline_admin(
    guide_id: str,
    body: GuidelineUpdate,
    admin: UserProfile = AdminRequired,
    guide_repo: GuideRepoDep = None,
    audit_repo: AuditRepoDep = None,
) -> GuidelineOut:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(guide, field, value)
    guide.updated_at = utcnow()
    updated = await guide_repo.update(guide)

    await audit_repo.create(AuditRecord(
        actor_id=admin.id,
        actor_email=admin.email,
        action=AuditAction.UPDATE,
        resource_type="guideline",
        resource_id=guide_id,
        description=f"Admin updated guideline {guide.title} to version {guide.version} ({guide.status})",
        metadata=update_data,
    ))
    return GuidelineOut.model_validate(updated.model_dump())


# ─── Document Metadata Management (admin-only) ────────────────────────────────

@router.patch("/documents/{doc_id}", response_model=DocumentOut,
              summary="Update document metadata (admin)")
async def update_document_metadata_admin(
    doc_id: str,
    body: DocumentUpdate,
    admin: UserProfile = AdminRequired,
    doc_repo: DocRepoDep = None,
    audit_repo: AuditRepoDep = None,
) -> DocumentOut:
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(doc, field, value)
    doc.updated_at = utcnow()
    doc.version += 1
    updated = await doc_repo.update(doc)

    await audit_repo.create(AuditRecord(
        actor_id=admin.id,
        actor_email=admin.email,
        action=AuditAction.UPDATE,
        resource_type="document",
        resource_id=doc_id,
        description=f"Admin updated document {doc.title} metadata (v{doc.version})",
        metadata=update_data,
    ))
    return DocumentOut.model_validate(updated.model_dump())


# ─── Learning Requirement Assignment (admin-only) ─────────────────────────────

@router.put("/learning/{resource_id}/requirements", response_model=LearningResourceOut,
            summary="Assign role-based learning requirements, prerequisites, and due days (admin)")
async def assign_learning_requirements(
    resource_id: str,
    body: LearningResourceUpdate,
    admin: UserProfile = AdminRequired,
    learning_repo: LearningRepoDep = None,
    audit_repo: AuditRepoDep = None,
) -> LearningResourceOut:
    resource = await learning_repo.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning resource not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    updated = await learning_repo.update_resource(resource) if hasattr(learning_repo, "update_resource") else await learning_repo.create_resource(resource)

    await audit_repo.create(AuditRecord(
        actor_id=admin.id,
        actor_email=admin.email,
        action=AuditAction.UPDATE,
        resource_type="learning_resource",
        resource_id=resource_id,
        description=f"Admin updated requirements for {resource.title}",
        metadata={"required_roles": [r.value for r in resource.required_for_roles]},
    ))
    return LearningResourceOut.model_validate(updated.model_dump())


# ─── Ingestion Errors & System Audit (admin-only) ──────────────────────────────

@router.get("/ingestion-errors", response_model=PaginatedResponse[AuditRecordOut],
            summary="View document ingestion errors and system warning events (admin)")
async def list_ingestion_errors(
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminRequired,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[AuditRecordOut]:
    skip = (page - 1) * page_size
    records, total = await audit_repo.list(skip=skip, limit=page_size)
    # Filter or prioritize records with error/failure or ingestion resource_type
    error_items = [
        r for r in records
        if "ingest" in (r.resource_type or "").lower()
        or "error" in (r.description or "").lower()
        or "fail" in (r.description or "").lower()
        or r.action in (AuditAction.AUTH_FAILURE, AuditAction.PERMISSION_DENIED)
    ]
    # If no explicitly tagged errors exist, return the audit trail records
    display_items = error_items if error_items else records[:page_size]
    return PaginatedResponse(
        items=[AuditRecordOut.model_validate(r.model_dump()) for r in display_items],
        total=len(display_items),
        page=page,
        page_size=page_size,
        has_next=False,
    )


# ─── Integrations Status (admin-only) ─────────────────────────────────────────

@router.get("/integrations/status", summary="Cloud and AI Integration Diagnostics (admin)")
async def admin_integrations_status(
    _: UserProfile = AdminRequired,
) -> dict:
    from .health import integrations_status
    return await integrations_status()


# ─── Reprocess Corrupted Documents (admin-only) ─────────────────────────────

@router.post("/reprocess-documents", summary="Reprocess and repair documents with legacy or unreadable content (admin)")
async def reprocess_documents(
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
    current_user: CurrentUser,
    _: UserProfile = AdminRequired,
) -> dict:
    from ..services.ingestion import get_ingestion
    ingestion = get_ingestion()
    docs, total = await doc_repo.list(skip=0, limit=200)
    repaired_ids = []

    stream_artifacts = ["/FlateDecode", "/Filter /", "/XObject", "endstream", "/Length "]
    for doc in docs:
        content = (doc.content or doc.extracted_text or "")
        if any(a in content for a in stream_artifacts) or (doc.file_type == "pdf" and not content.strip()):
            reprocessed = await ingestion.reprocess_document(doc)
            await doc_repo.update(reprocessed.id, reprocessed)
            repaired_ids.append(reprocessed.id)

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="document",
        description=f"Admin triggered document reprocessing: repaired {len(repaired_ids)} documents",
        metadata={"repaired_count": len(repaired_ids), "repaired_ids": repaired_ids},
    ))
    return {
        "status": "success",
        "scanned_count": total,
        "repaired_count": len(repaired_ids),
        "repaired_ids": repaired_ids,
    }

