"""
User management routes.
Admin-only write operations; authenticated reads for own profile.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import AdminRequired, CurrentUser
from ..dependencies import AuditRepoDep, DeptRepoDep, UserRepoDep
from ..models import AuditAction, AuditRecord, UserProfile, UserRole, UserStatus, utcnow
from ..schemas import (
    OrgNode,
    PaginatedResponse,
    UserCreate,
    UserPublic,
    UserSensitive,
    UserUpdate,
)
from ..auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _to_public(user: UserProfile) -> UserPublic:
    return UserPublic.model_validate(user.model_dump())


@router.get("", response_model=PaginatedResponse[UserPublic], summary="List all users (admin)")
async def list_users(
    current_user: CurrentUser,
    user_repo: UserRepoDep,
    _: UserProfile = AdminRequired,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[UserPublic]:
    skip = (page - 1) * page_size
    users, total = await user_repo.list(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[_to_public(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.get("/me", response_model=UserPublic, summary="Current user profile")
async def get_me(current_user: CurrentUser) -> UserPublic:
    return _to_public(current_user)


@router.get("/directory", response_model=list[UserPublic], summary="Employee directory (authenticated)")
async def get_directory(
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> list[UserPublic]:
    users, _ = await user_repo.list(limit=200)
    return [_to_public(u) for u in users]


@router.get("/{user_id}/sensitive", response_model=UserSensitive, summary="Sensitive employee profile details")
async def get_sensitive_details(
    user_id: str,
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> UserSensitive:
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Permission enforcement: Admin, line manager of target user, or target user themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_self = current_user.id == user_id
    is_manager = user.manager_id == current_user.id

    if not (is_admin or is_self or is_manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: You do not have permission to view sensitive HR details for this employee.",
        )

    return UserSensitive(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        department_name=user.department_name,
        job_title=user.job_title,
        manager_id=user.manager_id,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        employee_code=f"EMP-{user.id[-4:].upper()}-2026",
        clearance_level="Tier 3 Confidential" if user.role in (UserRole.ADMIN, UserRole.TECHNICAL_LEAD) else "Standard Internal",
        performance_rating="Exceeds Expectations" if user.role != UserRole.ADMIN else "Leadership Tier",
        onboarding_status="Completed" if user.status == UserStatus.ACTIVE else "In Progress",
        contract_type="Full-time Permanent",
        emergency_contact="+1 (555) 234-8901 (Family / Next of Kin)",
        salary_band=f"Level {4 if user.role == UserRole.SOFTWARE_DEVELOPER else 5 if user.role in (UserRole.TECHNICAL_LEAD, UserRole.PROJECT_MANAGER) else 6} Comprehensive",
    )


@router.get("/{user_id}", response_model=UserPublic, summary="Get user by ID")
async def get_user(
    user_id: str,
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> UserPublic:
    # Any authenticated user may view profiles; sensitive fields stripped by UserPublic.
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_public(user)


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED,
             summary="Create user (admin)")
async def create_user(
    body: UserCreate,
    user_repo: UserRepoDep,
    dept_repo: DeptRepoDep,
    audit_repo: AuditRepoDep,
    _: UserProfile = AdminRequired,
) -> UserPublic:
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")

    dept_name = None
    if body.department_id:
        dept = await dept_repo.get(body.department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Department not found")
        dept_name = dept.name

    user = UserProfile(
        email=body.email,
        name=body.name,
        role=body.role,
        department_id=body.department_id,
        department_name=dept_name,
        job_title=body.job_title,
        manager_id=body.manager_id,
        hashed_password=hash_password(body.password),
    )
    created = await user_repo.create(user)
    await audit_repo.create(AuditRecord(
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id=created.id,
        description=f"Admin created user {created.email}",
    ))
    return _to_public(created)


@router.patch("/{user_id}", response_model=UserPublic, summary="Update user (admin or self)")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: CurrentUser,
    user_repo: UserRepoDep,
    dept_repo: DeptRepoDep,
    audit_repo: AuditRepoDep,
) -> UserPublic:
    # Self-update allowed; role changes require admin.
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Cannot modify another user's profile")

    if body.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only admins may change roles")

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    if body.department_id:
        dept = await dept_repo.get(body.department_id)
        if dept:
            user.department_name = dept.name

    updated = await user_repo.update(user)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user_id,
        description=f"Updated user {updated.email}",
        metadata=update_data,
    ))
    return _to_public(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete user (admin)")
async def delete_user(
    user_id: str,
    user_repo: UserRepoDep,
    audit_repo: AuditRepoDep,
    current_user: UserProfile = AdminRequired,
) -> Response:
    if not await user_repo.delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.DELETE,
        resource_type="user",
        resource_id=user_id,
        description=f"Deleted user {user_id}",
    ))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/reports", response_model=list[UserPublic],
            summary="Direct reports for a user")
async def get_reports(
    user_id: str,
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> list[UserPublic]:
    reports = await user_repo.list_reports(manager_id=user_id)
    return [_to_public(u) for u in reports]


@router.get("/org/tree", response_model=list[OrgNode], summary="Full org-chart tree")
async def org_tree(
    current_user: CurrentUser,
    user_repo: UserRepoDep,
) -> list[OrgNode]:
    users, _ = await user_repo.list(limit=200)
    user_map = {u.id: u for u in users}

    def build_node(user: UserProfile) -> OrgNode:
        children = [build_node(u) for u in users if u.manager_id == user.id]
        return OrgNode(user=UserPublic.model_validate(user.model_dump()), reports=children)

    # Root nodes: users with no manager
    roots = [u for u in users if u.manager_id is None]
    return [build_node(r) for r in roots]
