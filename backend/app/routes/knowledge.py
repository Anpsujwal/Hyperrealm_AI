"""
Knowledge hub routes — documents and guidelines.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser, LeadOrAbove
from ..dependencies import AuditRepoDep, DocRepoDep, GuideRepoDep
from ..models import AuditAction, AuditRecord, Document, Guideline, UserProfile, utcnow
from ..schemas import (
    DocumentCreate,
    DocumentOut,
    GuidelineCreate,
    GuidelineOut,
    PaginatedResponse,
)

router = APIRouter(tags=["knowledge"])


# ─── Documents ────────────────────────────────────────────────────────────────

@router.get("/documents", response_model=PaginatedResponse[DocumentOut], summary="List documents")
async def list_documents(
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
) -> PaginatedResponse[DocumentOut]:
    skip = (page - 1) * page_size
    docs, total = await doc_repo.list(skip=skip, limit=page_size, category=category)
    return PaginatedResponse(
        items=[DocumentOut.model_validate(d.model_dump()) for d in docs],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED,
             summary="Create document")
async def create_document(
    body: DocumentCreate,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
) -> DocumentOut:
    doc = Document(**body.model_dump(), author_id=current_user.id)
    created = await doc_repo.create(doc)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="document",
        resource_id=created.id,
        description=f"Created document: {created.title}",
    ))
    return DocumentOut.model_validate(created.model_dump())


@router.get("/documents/{doc_id}", response_model=DocumentOut, summary="Get document")
async def get_document(
    doc_id: str,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
) -> DocumentOut:
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentOut.model_validate(doc.model_dump())


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete document (author or admin)")
async def delete_document(
    doc_id: str,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
) -> Response:
    from ..models import UserRole
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the author or an admin may delete this document")
    await doc_repo.delete(doc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Guidelines ───────────────────────────────────────────────────────────────

@router.get("/guidelines", response_model=PaginatedResponse[GuidelineOut],
            summary="List guidelines")
async def list_guidelines(
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
) -> PaginatedResponse[GuidelineOut]:
    skip = (page - 1) * page_size
    guides, total = await guide_repo.list(skip=skip, limit=page_size, category=category)
    return PaginatedResponse(
        items=[GuidelineOut.model_validate(g.model_dump()) for g in guides],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/guidelines", response_model=GuidelineOut, status_code=status.HTTP_201_CREATED,
             summary="Create guideline (lead or above)")
async def create_guideline(
    body: GuidelineCreate,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = LeadOrAbove,
) -> GuidelineOut:
    guide = Guideline(**body.model_dump(), owner_id=current_user.id)
    created = await guide_repo.create(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="guideline",
        resource_id=created.id,
        description=f"Created guideline: {created.title}",
    ))
    return GuidelineOut.model_validate(created.model_dump())


@router.get("/guidelines/{guide_id}", response_model=GuidelineOut, summary="Get guideline")
async def get_guideline(
    guide_id: str,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
) -> GuidelineOut:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    return GuidelineOut.model_validate(guide.model_dump())
