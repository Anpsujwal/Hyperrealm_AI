"""
Learning resources routes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..auth import CurrentUser, LeadOrAbove
from ..dependencies import LearningRepoDep
from ..models import LearningResource, LearningStatus, UserLearningProgress, UserProfile, utcnow
from ..schemas import (
    LearningProgressOut,
    LearningProgressUpdate,
    LearningResourceCreate,
    LearningResourceOut,
    PaginatedResponse,
)

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/resources", response_model=PaginatedResponse[LearningResourceOut],
            summary="List learning resources")
async def list_resources(
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[LearningResourceOut]:
    skip = (page - 1) * page_size
    resources, total = await learning_repo.list_resources(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[LearningResourceOut.model_validate(r.model_dump()) for r in resources],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/resources", response_model=LearningResourceOut,
             status_code=status.HTTP_201_CREATED, summary="Create resource (lead or above)")
async def create_resource(
    body: LearningResourceCreate,
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
    _: UserProfile = LeadOrAbove,
) -> LearningResourceOut:
    resource = LearningResource(**body.model_dump())
    created = await learning_repo.create_resource(resource)
    return LearningResourceOut.model_validate(created.model_dump())


@router.get("/resources/{resource_id}", response_model=LearningResourceOut,
            summary="Get resource")
async def get_resource(
    resource_id: str,
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
) -> LearningResourceOut:
    resource = await learning_repo.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Learning resource not found")
    return LearningResourceOut.model_validate(resource.model_dump())


@router.get("/progress/me", response_model=list[LearningProgressOut],
            summary="My learning progress")
@router.get("/my-progress", response_model=list[LearningProgressOut],
            summary="My learning progress alias")
async def my_progress(
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
) -> list[LearningProgressOut]:
    items = await learning_repo.list_progress_by_user(current_user.id)
    return [LearningProgressOut.model_validate(p.model_dump()) for p in items]


@router.get("/paths", summary="Enriched role-specific learning paths with mandatory status, prerequisites, and progress")
async def get_learning_paths(
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
    role: str | None = None,
) -> dict:
    from datetime import timedelta
    target_role = role or current_user.role.value
    resources, _ = await learning_repo.list_resources(limit=100)
    user_progress_list = await learning_repo.list_progress_by_user(current_user.id)
    progress_map = {p.resource_id: p for p in user_progress_list}
    completed_ids = {p.resource_id for p in user_progress_list if p.status == LearningStatus.COMPLETED}

    items = []
    for r in resources:
        req_role_strs = [r_role.value if hasattr(r_role, "value") else str(r_role) for r_role in r.required_for_roles]
        is_mandatory = target_role in req_role_strs or "employee" in req_role_strs
        prog = progress_map.get(r.id)
        prereqs_met = all(p_id in completed_ids for p_id in r.prerequisites) if r.prerequisites else True
        due_dt = prog.due_date if prog and prog.due_date else (current_user.created_at + timedelta(days=r.due_days or 30))

        items.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "category": r.category,
            "url": r.url,
            "estimated_minutes": r.estimated_minutes,
            "required_for_roles": req_role_strs,
            "tags": r.tags,
            "prerequisites": r.prerequisites,
            "prerequisites_met": prereqs_met,
            "due_days": r.due_days,
            "due_date": due_dt.isoformat() if due_dt else None,
            "is_mandatory": is_mandatory,
            "status": prog.status.value if prog else "not_started",
            "progress_pct": prog.progress_pct if prog else 0,
            "started_at": prog.started_at.isoformat() if prog and prog.started_at else None,
            "completed_at": prog.completed_at.isoformat() if prog and prog.completed_at else None,
        })

    return {
        "role": target_role,
        "total": len(items),
        "mandatory_count": sum(1 for i in items if i["is_mandatory"]),
        "completed_count": sum(1 for i in items if i["status"] == "completed"),
        "in_progress_count": sum(1 for i in items if i["status"] == "in_progress"),
        "items": items,
    }


@router.put("/resources/{resource_id}/progress", response_model=LearningProgressOut,
            summary="Update my progress on a resource")
async def update_progress(
    resource_id: str,
    body: LearningProgressUpdate,
    current_user: CurrentUser,
    learning_repo: LearningRepoDep,
) -> LearningProgressOut:
    resource = await learning_repo.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Learning resource not found")

    existing = await learning_repo.get_progress(current_user.id, resource_id)
    if existing:
        existing.status = body.status
        existing.progress_pct = body.progress_pct
        existing.updated_at = utcnow()
        if body.status == LearningStatus.COMPLETED and not existing.completed_at:
            existing.completed_at = utcnow()
        if body.status == LearningStatus.IN_PROGRESS and not existing.started_at:
            existing.started_at = utcnow()
        progress = existing
    else:
        progress = UserLearningProgress(
            user_id=current_user.id,
            resource_id=resource_id,
            status=body.status,
            progress_pct=body.progress_pct,
            started_at=utcnow() if body.status != LearningStatus.NOT_STARTED else None,
            completed_at=utcnow() if body.status == LearningStatus.COMPLETED else None,
        )

    saved = await learning_repo.upsert_progress(progress)
    return LearningProgressOut.model_validate(saved.model_dump())
