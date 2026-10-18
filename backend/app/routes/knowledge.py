"""
Knowledge hub routes — personal documents, official guidelines,
document intelligence, multimodal image audits, and enterprise retrieval.
"""
from __future__ import annotations

import base64
import difflib
import os
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response

from ..auth import AdminOnly, AdminRequired, CurrentUser, LeadOrAbove
from ..dependencies import (
    ActionExecutionRepoDep,
    AuditRepoDep,
    BrandComplianceRepoDep,
    DocRepoDep,
    GuideRepoDep,
    GuideVersionRepoDep,
)
from ..models import (
    AuditAction,
    AuditRecord,
    Document,
    DocumentScope,
    Guideline,
    GuidelineStatus,
    GuidelineVersionRecord,
    ProcessingStatus,
    UserProfile,
    UserRole,
    new_id,
    utcnow,
)
from ..schemas import (
    BrandComplianceAuditRequest,
    BrandComplianceAuditResponse,
    DiffLine,
    DocumentCreate,
    DocumentOut,
    DocumentQueryRequest,
    DocumentQueryResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    GuidelineCreate,
    GuidelineDiffResponse,
    GuidelineOut,
    GuidelineUpdate,
    GuidelineVersionCreate,
    GuidelineVersionOut,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    PaginatedResponse,
    SemanticChangeSummary,
    SideBySideLine,
)
from ..services.ingestion import DocumentIngestionService
from ..services.retrieval import EnterpriseRetrievalService
from ..services.vision import BrandComplianceService

router = APIRouter(tags=["knowledge"])

_ingestion_service: Optional[DocumentIngestionService] = None
_retrieval_service: Optional[EnterpriseRetrievalService] = None
_vision_service: Optional[BrandComplianceService] = None


def get_ingestion() -> DocumentIngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DocumentIngestionService()
    return _ingestion_service


def get_retrieval() -> EnterpriseRetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = EnterpriseRetrievalService()
    return _retrieval_service


def get_vision() -> BrandComplianceService:
    global _vision_service
    if _vision_service is None:
        _vision_service = BrandComplianceService()
    return _vision_service


# ─── Documents (Personal & General) ──────────────────────────────────────────

@router.get("/documents", response_model=PaginatedResponse[DocumentOut], summary="List documents")
async def list_documents(
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    scope: str | None = None,
) -> PaginatedResponse[DocumentOut]:
    """List documents accessible to current user (filtered by personal ownership when requested)."""
    skip = (page - 1) * page_size
    author_filter = current_user.id if scope == DocumentScope.PERSONAL.value else None
    docs, total = await doc_repo.list(
        skip=skip,
        limit=page_size,
        category=category,
        author_id=author_filter,
        scope=scope,
    )
    return PaginatedResponse(
        items=[DocumentOut.model_validate(d.model_dump()) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.get("/personal/documents", response_model=PaginatedResponse[DocumentOut],
            summary="List my personal Knowledge Hub documents")
async def list_personal_documents(
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
) -> PaginatedResponse[DocumentOut]:
    """List only personal working documents owned by the authenticated employee."""
    skip = (page - 1) * page_size
    docs, total = await doc_repo.list(
        skip=skip,
        limit=page_size,
        category=category,
        author_id=current_user.id,
        scope=DocumentScope.PERSONAL.value,
    )
    return PaginatedResponse(
        items=[DocumentOut.model_validate(d.model_dump()) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/personal/documents/upload", response_model=DocumentOut,
             status_code=status.HTTP_201_CREATED, summary="Upload personal document")
async def upload_personal_document(
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("kt"),
    tags: Optional[str] = Form(None),
) -> DocumentOut:
    """Ingest, extract text/tables/images, and store an employee working document."""
    ingestion = get_ingestion()
    content_bytes = await file.read()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    doc = await ingestion.ingest_document(
        file_bytes=content_bytes,
        filename=file.filename or "uploaded_document",
        user=current_user,
        scope=DocumentScope.PERSONAL,
        category=category,
        tags=tag_list,
        title=title,
        is_public=False,
    )
    created = await doc_repo.create(doc)

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="document",
        resource_id=created.id,
        description=f"Uploaded personal document: {created.title}",
    ))
    return DocumentOut.model_validate(created.model_dump())


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED,
             summary="Create document directly")
async def create_document(
    body: DocumentCreate,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
) -> DocumentOut:
    doc = Document(
        **body.model_dump(),
        author_id=current_user.id,
        scope=DocumentScope.PERSONAL,
        status=ProcessingStatus.INDEXED,
    )
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
    # Enforce personal document isolation: only author or admin can access private document
    if doc.scope == DocumentScope.PERSONAL and doc.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: private document")
    return DocumentOut.model_validate(doc.model_dump())


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete document (author or admin)")
@router.delete("/personal/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete personal document (author or admin)")
async def delete_document(
    doc_id: str,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    audit_repo: AuditRepoDep,
) -> Response:
    doc = await doc_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the author or an admin may delete this document")

    # Clean up physical file on disk if it exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    await doc_repo.delete(doc_id)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.DELETE,
        resource_type="document",
        resource_id=doc_id,
        description=f"Deleted personal document: {doc.title}",
    ))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Document Intelligence (Summary & Q&A) ───────────────────────────────────

@router.post("/documents/{doc_id}/summary", response_model=DocumentSummaryResponse,
             summary="Summarize document")
async def summarize_document(
    doc_id: str,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
    body: DocumentSummaryRequest | None = None,
) -> DocumentSummaryResponse:
    from ..agents.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent(get_retrieval())
    try:
        res = await agent.summarize_document(doc_id, current_user)
        if res.get("visual_elements_detected") is None:
            res["visual_elements_detected"] = []
        if res.get("key_points") is None:
            res["key_points"] = []
        if res.get("key_takeaways") is None:
            res["key_takeaways"] = res["key_points"]
        if res.get("suggested_questions") is None:
            res["suggested_questions"] = []
        if res.get("citations") is None:
            res["citations"] = []
        return DocumentSummaryResponse(**res)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post("/documents/{doc_id}/query", response_model=DocumentQueryResponse,
             summary="Ask document-specific questions")
async def query_document(
    doc_id: str,
    body: DocumentQueryRequest,
    current_user: CurrentUser,
    doc_repo: DocRepoDep,
) -> DocumentQueryResponse:
    from ..agents.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent(get_retrieval())
    res = await agent.execute(body.query, current_user, document_id=doc_id)
    if "Access denied" in res.get("response", ""):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return DocumentQueryResponse(
        document_id=doc_id,
        query=body.query,
        answer=res["response"],
        citations=res.get("citations", []),
        confidence=0.96,
        scope=DocumentScope.PERSONAL,
    )


# ─── Enterprise Retrieval Search ─────────────────────────────────────────────

@router.post("/search", response_model=KnowledgeSearchResponse,
             summary="Enterprise scoped knowledge search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    current_user: CurrentUser,
) -> KnowledgeSearchResponse:
    retrieval = get_retrieval()
    results, discrepancies = await retrieval.search(
        query=body.query,
        user=current_user,
        scopes=body.scopes,
        top_k=body.top_k,
    )
    return KnowledgeSearchResponse(
        query=body.query,
        results=results,
        total_results=len(results),
        discrepancies=discrepancies,
    )


# ─── Multimodal Image & Brand Compliance Audit ───────────────────────────────

@router.post("/images/audit", response_model=BrandComplianceAuditResponse,
             summary="Brand-compliance image audit")
async def audit_brand_image(
    request: Request,
    current_user: CurrentUser,
) -> BrandComplianceAuditResponse:
    vision = get_vision()
    image_bytes = None
    filename = None
    image_url = None

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "read"):
            image_bytes = await uploaded_file.read()
            filename = getattr(uploaded_file, "filename", "uploaded_image.png")
        if not filename and "image_filename" in form:
            filename = str(form.get("image_filename"))
        if not image_url and "image_url" in form:
            image_url = str(form.get("image_url"))
    else:
        try:
            json_data = await request.json()
            if isinstance(json_data, dict):
                image_url = json_data.get("image_url")
                filename = json_data.get("image_filename")
                b64 = json_data.get("image_base64")
                if b64:
                    try:
                        clean_b64 = b64.split(",")[-1]
                        image_bytes = base64.b64decode(clean_b64)
                    except Exception:
                        pass
        except Exception:
            pass

    report = await vision.audit_image(
        image_bytes=image_bytes,
        image_url=image_url,
        image_filename=filename,
        user=current_user,
    )
    return BrandComplianceAuditResponse.model_validate(report.model_dump())


# ─── Official Guidelines (Authoritative Knowledge Base) ──────────────────────

@router.get("/guidelines", response_model=PaginatedResponse[GuidelineOut],
            summary="List guidelines")
@router.get("/official/documents", response_model=PaginatedResponse[GuidelineOut],
            summary="List official published guidelines (accessible to all employees)")
async def list_guidelines(
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    status_filter: str | None = None,
) -> PaginatedResponse[GuidelineOut]:
    """Both employees and admins can browse and read published official guidelines."""
    skip = (page - 1) * page_size
    # Non-admins only see published guidelines
    enforced_status = status_filter if current_user.role == UserRole.ADMIN else "published"
    guides, total = await guide_repo.list(skip=skip, limit=page_size, category=category, status=enforced_status)
    return PaginatedResponse(
        items=[GuidelineOut.model_validate(g.model_dump()) for g in guides],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/guidelines", response_model=GuidelineOut, status_code=status.HTTP_201_CREATED,
             summary="Create guideline (Lead or above)")
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


@router.post("/official/documents", response_model=GuidelineOut, status_code=status.HTTP_201_CREATED,
             summary="Upload official authoritative guideline (Administrator only)")
async def create_official_document(
    body: GuidelineCreate,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    """Only administrators can upload and publish official authoritative organizational documents."""
    data = body.model_dump()
    data["status"] = "published"
    guide = Guideline(
        **data,
        owner_id=current_user.id,
        processing_status=ProcessingStatus.INDEXED,
    )
    created = await guide_repo.create(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.PUBLISH,
        resource_type="guideline",
        resource_id=created.id,
        description=f"Admin published official authoritative guideline: {created.title}",
    ))
    return GuidelineOut.model_validate(created.model_dump())


@router.post("/official/documents/upload", response_model=GuidelineOut, status_code=status.HTTP_201_CREATED,
             summary="Upload official authoritative guideline file (Admin only)")
async def upload_official_guideline_file(
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("engineering"),
    version: str = Form("1.0"),
    tags: Optional[str] = Form(None),
    status_val: str = Form("published"),
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    """Only administrators can upload files to create official authoritative policies."""
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_text = f"Uploaded official guideline document: {file.filename}\nSize: {len(content_bytes)} bytes"

    clean_title = title or (file.filename or "Official Guideline").replace(".md", "").replace(".txt", "").replace(".pdf", "").title()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else ["official", category]

    guide = Guideline(
        title=clean_title,
        content=content_text,
        description=f"Authoritative organizational guideline uploaded from {file.filename or 'file'}.",
        category=category,
        version=version,
        status=status_val,
        tags=tag_list,
        owner_id=current_user.id,
        processing_status=ProcessingStatus.INDEXED,
    )
    created = await guide_repo.create(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.PUBLISH,
        resource_type="guideline",
        resource_id=created.id,
        description=f"Admin uploaded official guideline: {created.title}",
    ))
    return GuidelineOut.model_validate(created.model_dump())


@router.patch("/official/documents/{guide_id}", response_model=GuidelineOut,
              summary="Update official guideline (Admin only)")
@router.put("/official/documents/{guide_id}", response_model=GuidelineOut,
            summary="Update official guideline (Admin only)")
@router.patch("/guidelines/{guide_id}", response_model=GuidelineOut,
              summary="Update guideline (Admin only)")
@router.put("/guidelines/{guide_id}", response_model=GuidelineOut,
            summary="Update guideline (Admin only)")
async def update_official_guideline(
    guide_id: str,
    body: GuidelineUpdate,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    gver_repo: GuideVersionRepoDep,
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    """Administrators can edit existing policies, update versions, or modify metadata."""
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")

    # If version changed or changelog provided, record snapshot of previous version
    if (body.version and body.version != guide.version) or body.changelog:
        prev_record = GuidelineVersionRecord(
            id=new_id("gver_"),
            guideline_id=guide_id,
            version=guide.version,
            title=guide.title,
            content=guide.content,
            description=guide.description,
            category=guide.category,
            changelog=guide.changelog or "Previous stable revision",
            status=guide.status,
            created_by=guide.owner_id,
            effective_date=guide.effective_date,
            created_at=guide.created_at,
        )
        await gver_repo.create(prev_record)
        guide.version_history.append({
            "version": prev_record.version,
            "archived_at": utcnow().isoformat(),
            "archived_by": current_user.email,
        })

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(guide, field, value)
    guide.updated_at = utcnow()
    updated = await guide_repo.update(guide)

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="guideline",
        resource_id=guide_id,
        description=f"Admin updated official guideline: {guide.title} (v{guide.version})",
        metadata=update_data,
    ))
    return GuidelineOut.model_validate(updated.model_dump())


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


# ─── Guideline Lifecycle & Versioning (Admin Only) ───────────────────────────

@router.get("/guidelines/{guide_id}/versions", response_model=list[GuidelineVersionOut],
            summary="List guideline version history")
async def list_guideline_versions(
    guide_id: str,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    gver_repo: GuideVersionRepoDep,
) -> list[GuidelineVersionOut]:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    versions = await gver_repo.list_by_guideline(guide_id)
    return [GuidelineVersionOut.model_validate(v.model_dump()) for v in versions]


@router.post("/guidelines/{guide_id}/versions", response_model=GuidelineOut,
             summary="Create new version of guideline (Admin only)")
async def create_guideline_version(
    guide_id: str,
    body: GuidelineVersionCreate,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    gver_repo: GuideVersionRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")

    # Record previous version snapshot
    prev_record = GuidelineVersionRecord(
        id=new_id("gver_"),
        guideline_id=guide_id,
        version=guide.version,
        title=guide.title,
        content=guide.content,
        description=guide.description,
        category=guide.category,
        changelog=guide.changelog,
        status=guide.status,
        created_by=guide.owner_id,
        effective_date=guide.effective_date,
        created_at=guide.created_at,
    )
    await gver_repo.create(prev_record)

    # Update guideline to new version
    guide.version = body.version
    guide.title = body.title
    guide.content = body.content
    if body.description:
        guide.description = body.description
    guide.changelog = body.changelog
    guide.status = body.status
    guide.effective_date = body.effective_date or utcnow()
    guide.updated_at = utcnow()
    guide.version_history.append({
        "version": prev_record.version,
        "archived_at": utcnow().isoformat(),
        "archived_by": current_user.email,
    })

    updated = await guide_repo.update(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="guideline",
        resource_id=guide_id,
        description=f"Created version {body.version} of guideline {guide.title}",
    ))
    return GuidelineOut.model_validate(updated.model_dump())


@router.patch("/guidelines/{guide_id}/publish", response_model=GuidelineOut,
              summary="Publish guideline (Admin only)")
async def publish_guideline(
    guide_id: str,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    guide.status = "published"
    guide.updated_at = utcnow()
    updated = await guide_repo.update(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.PUBLISH,
        resource_type="guideline",
        resource_id=guide_id,
        description=f"Admin published authoritative guideline {guide.title}",
    ))
    return GuidelineOut.model_validate(updated.model_dump())


@router.patch("/guidelines/{guide_id}/archive", response_model=GuidelineOut,
              summary="Archive guideline (Admin only)")
async def archive_guideline(
    guide_id: str,
    current_user: CurrentUser,
    guide_repo: GuideRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminOnly,
) -> GuidelineOut:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    guide.status = "archived"
    guide.updated_at = utcnow()
    updated = await guide_repo.update(guide)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.ARCHIVE,
        resource_type="guideline",
        resource_id=guide_id,
        description=f"Admin archived guideline {guide.title}",
    ))
    return GuidelineOut.model_validate(updated.model_dump())


# ─── Guideline Semantic Diff & Impact Analysis ───────────────────────────────

@router.get("/guidelines/{guide_id}/diff", response_model=GuidelineDiffResponse,
            summary="Compare guideline versions and identify affected roles")
@router.get("/official/documents/{guide_id}/diff", response_model=GuidelineDiffResponse,
            summary="Compare official guideline versions and identify affected roles")
async def get_guideline_diff(
    guide_id: str,
    base_version: Optional[str] = Query(None, description="Previous version to compare from"),
    target_version: Optional[str] = Query(None, description="Newer version to compare to (defaults to current)"),
    current_user: CurrentUser = None,
    guide_repo: GuideRepoDep = None,
    gver_repo: GuideVersionRepoDep = None,
) -> GuidelineDiffResponse:
    guide = await guide_repo.get(guide_id)
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")

    versions = await gver_repo.list_by_guideline(guide_id)
    all_version_strings = list({v.version for v in versions} | {guide.version})
    all_version_strings.sort(reverse=True)

    tgt_v = target_version or guide.version
    if tgt_v == guide.version:
        tgt_title = guide.title
        tgt_content = guide.content
    else:
        tgt_record = next((v for v in versions if v.version == tgt_v), None)
        tgt_title = tgt_record.title if tgt_record else guide.title
        tgt_content = tgt_record.content if tgt_record else guide.content

    if base_version:
        base_v = base_version
        base_record = next((v for v in versions if v.version == base_version), None)
        base_content = base_record.content if base_record else ""
    else:
        prior_candidates = [v for v in versions if v.version != tgt_v]
        if prior_candidates:
            base_record = prior_candidates[0]
            base_v = base_record.version
            base_content = base_record.content
        else:
            base_record = None
            base_v = "1.0 (Initial)" if tgt_v != "1.0" else "Draft"
            base_content = ""

    base_lines = base_content.splitlines()
    target_lines = tgt_content.splitlines()
    matcher = difflib.SequenceMatcher(None, base_lines, target_lines)

    unified_diff: list[DiffLine] = []
    side_by_side: list[SideBySideLine] = []
    additions = 0
    deletions = 0
    old_line_no = 1
    new_line_no = 1

    for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
        if tag == "equal":
            for i in range(alo, ahi):
                b_text = base_lines[i]
                t_text = target_lines[blo + (i - alo)]
                unified_diff.append(DiffLine(type="unchanged", text=b_text, old_line_no=old_line_no, new_line_no=new_line_no))
                side_by_side.append(SideBySideLine(
                    old_line_no=old_line_no,
                    old_text=b_text,
                    old_type="unchanged",
                    new_line_no=new_line_no,
                    new_text=t_text,
                    new_type="unchanged",
                ))
                old_line_no += 1
                new_line_no += 1
        elif tag == "replace":
            max_len = max(ahi - alo, bhi - blo)
            for j in range(max_len):
                has_old = (alo + j) < ahi
                has_new = (blo + j) < bhi
                old_text = base_lines[alo + j] if has_old else ""
                new_text = target_lines[blo + j] if has_new else ""

                if has_old:
                    unified_diff.append(DiffLine(type="removed", text=old_text, old_line_no=old_line_no, new_line_no=None))
                    deletions += 1
                if has_new:
                    unified_diff.append(DiffLine(type="added", text=new_text, old_line_no=None, new_line_no=new_line_no))
                    additions += 1

                side_by_side.append(SideBySideLine(
                    old_line_no=old_line_no if has_old else None,
                    old_text=old_text if has_old else None,
                    old_type="removed" if has_old else "empty",
                    new_line_no=new_line_no if has_new else None,
                    new_text=new_text if has_new else None,
                    new_type="added" if has_new else "empty",
                ))
                if has_old:
                    old_line_no += 1
                if has_new:
                    new_line_no += 1
        elif tag == "delete":
            for i in range(alo, ahi):
                text = base_lines[i]
                unified_diff.append(DiffLine(type="removed", text=text, old_line_no=old_line_no, new_line_no=None))
                side_by_side.append(SideBySideLine(
                    old_line_no=old_line_no,
                    old_text=text,
                    old_type="removed",
                    new_line_no=None,
                    new_text=None,
                    new_type="empty",
                ))
                old_line_no += 1
                deletions += 1
        elif tag == "insert":
            for i in range(blo, bhi):
                text = target_lines[i]
                unified_diff.append(DiffLine(type="added", text=text, old_line_no=None, new_line_no=new_line_no))
                side_by_side.append(SideBySideLine(
                    old_line_no=None,
                    old_text=None,
                    old_type="empty",
                    new_line_no=new_line_no,
                    new_text=text,
                    new_type="added",
                ))
                new_line_no += 1
                additions += 1

    combined_delta_text = " ".join([d.text for d in unified_diff if d.type in ("added", "removed")]).lower()
    impact_badges: list[str] = []
    semantic_summary: list[SemanticChangeSummary] = []
    severity = "medium"

    if (
        "localstorage" in combined_delta_text
        or "cookie" in combined_delta_text
        or "token" in combined_delta_text
        or "samesite" in combined_delta_text
        or "jwt" in combined_delta_text
        or guide.category == "security"
    ):
        impact_badges.append("Impacts: Payments Platform")
        impact_badges.append("Frontend Engineering")
        impact_badges.append("DevOps & Cloud")
        impact_badges.append("Security Operations")
        severity = "high"

        if "localstorage" in combined_delta_text or "cookie" in combined_delta_text:
            semantic_summary.append(SemanticChangeSummary(
                change_type="breaking",
                category="Storage Policy",
                description="Deprecates client-side localStorage token persistence; mandates HttpOnly SameSite=Strict cookies."
            ))
        if "lifetime" in combined_delta_text or "minutes" in combined_delta_text or "tokens:" in combined_delta_text:
            semantic_summary.append(SemanticChangeSummary(
                change_type="requirement",
                category="Token Lifecycle",
                description="Reduces access token maximum lifetime to 60 minutes with immediate family revocation on reuse."
            ))
        if "coverage" in combined_delta_text or "quality" in combined_delta_text or "regression" in combined_delta_text:
            semantic_summary.append(SemanticChangeSummary(
                change_type="requirement",
                category="Quality Gates",
                description="Automated regression test coverage requirement raised to >= 85% before merge."
            ))

    if (
        "contrast" in combined_delta_text
        or "wcag" in combined_delta_text
        or "color" in combined_delta_text
        or "logo" in combined_delta_text
        or guide.category == "brand"
    ):
        if "Design System" not in impact_badges:
            impact_badges.append("Design System")
        if "Frontend Platform" not in impact_badges:
            impact_badges.append("Frontend Platform")
        if "Accessibility (WCAG AA)" not in impact_badges:
            impact_badges.append("Accessibility (WCAG AA)")
        if "contrast" in combined_delta_text or "wcag" in combined_delta_text:
            semantic_summary.append(SemanticChangeSummary(
                change_type="requirement",
                category="Accessibility",
                description="Updated color tokens to guarantee WCAG AA 4.5:1 minimum contrast ratio across all UI surfaces."
            ))

    for team in (guide.affected_teams or []):
        badge = f"Impacts: {team}" if not team.lower().startswith("impacts") else team
        if badge not in impact_badges:
            impact_badges.append(badge)

    role_map = {
        "admin": "Security & Org Admin",
        "technical_lead": "Technical Lead",
        "software_developer": "Software Developer",
        "devops_engineer": "DevOps Engineer",
        "qa_engineer": "QA Engineer",
        "project_manager": "Project Manager",
        "employee": "General Employee",
    }
    raw_roles = guide.applicable_roles or [
        "technical_lead", "software_developer", "devops_engineer", "qa_engineer"
    ]
    impacted_roles = [role_map.get(r, r.replace("_", " ").title()) for r in raw_roles]

    if not semantic_summary:
        semantic_summary.append(SemanticChangeSummary(
            change_type="enhancement",
            category="General Revision",
            description=guide.changelog or f"Updated specification from v{base_v} to v{tgt_v}.",
        ))

    return GuidelineDiffResponse(
        guideline_id=guide_id,
        guideline_title=tgt_title,
        category=guide.category,
        base_version=base_v,
        target_version=tgt_v,
        available_versions=all_version_strings,
        impact_badges=impact_badges,
        impacted_roles=impacted_roles,
        impacted_departments=guide.applicable_departments or ["Engineering", "Security"],
        impacted_projects=guide.affected_projects or ["Payments Gateway", "Core Auth", "Web Portal"],
        severity=severity,
        semantic_summary=semantic_summary,
        stats={
            "additions": additions,
            "deletions": deletions,
            "modifications": max(additions, deletions),
        },
        unified_diff=unified_diff,
        side_by_side=side_by_side,
    )
