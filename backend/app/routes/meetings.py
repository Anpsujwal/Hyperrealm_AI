"""
Meetings routes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser
from ..dependencies import AuditRepoDep, MeetingRepoDep
from ..models import AuditAction, AuditRecord, Meeting, utcnow
from ..schemas import (
    MeetingCreate,
    MeetingOut,
    MeetingUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=PaginatedResponse[MeetingOut], summary="List meetings")
async def list_meetings(
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mine: bool = False,
) -> PaginatedResponse[MeetingOut]:
    skip = (page - 1) * page_size
    meetings, total = await meeting_repo.list(
        skip=skip, limit=page_size,
        user_id=current_user.id if mine else None,
    )
    return PaginatedResponse(
        items=[MeetingOut.model_validate(m.model_dump()) for m in meetings],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED,
             summary="Schedule a meeting")
async def create_meeting(
    body: MeetingCreate,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    audit_repo: AuditRepoDep,
) -> MeetingOut:
    meeting = Meeting(**body.model_dump(), organiser_id=current_user.id)
    created = await meeting_repo.create(meeting)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="meeting",
        resource_id=created.id,
        description=f"Scheduled meeting: {created.title}",
    ))
    return MeetingOut.model_validate(created.model_dump())


@router.get("/{meeting_id}", response_model=MeetingOut, summary="Get meeting")
async def get_meeting(
    meeting_id: str,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
) -> MeetingOut:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return MeetingOut.model_validate(meeting.model_dump())


@router.patch("/{meeting_id}", response_model=MeetingOut, summary="Update meeting")
async def update_meeting(
    meeting_id: str,
    body: MeetingUpdate,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    audit_repo: AuditRepoDep,
) -> MeetingOut:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.organiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the organiser may update this meeting")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(meeting, field, value)
    meeting.updated_at = utcnow()
    updated = await meeting_repo.update(meeting)
    return MeetingOut.model_validate(updated.model_dump())


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete meeting")
async def delete_meeting(
    meeting_id: str,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    audit_repo: AuditRepoDep,
) -> Response:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.organiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the organiser may delete this meeting")
    await meeting_repo.delete(meeting_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
