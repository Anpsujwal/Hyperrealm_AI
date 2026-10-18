"""
Meetings routes with Calendar Collision Detection, RSVP Notifications, and Automatic Rescheduling.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser
from ..dependencies import AuditRepoDep, MeetingRepoDep, NotifRepoDep, UserRepoDep
from ..models import (
    AuditAction,
    AuditRecord,
    Meeting,
    MeetingStatus,
    Notification,
    NotificationType,
    utcnow,
)
from ..schemas import (
    CalendarAvailabilityRequest,
    CalendarAvailabilityResponse,
    MeetingConflict,
    MeetingCreate,
    MeetingOut,
    MeetingRsvpRequest,
    MeetingRsvpResponse,
    MeetingUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


# ─── Calendar Collision & Availability Helpers ─────────────────────────────────

def _normalize_dt(dt: datetime) -> datetime:
    """Ensure datetime is naive UTC for safe comparison."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def _find_conflicts(
    meeting_repo: Any,
    user_repo: Optional[Any],
    scheduled_at: datetime,
    duration_minutes: int,
    participant_ids: set[str],
    exclude_meeting_id: Optional[str] = None,
) -> list[MeetingConflict]:
    """Find any overlapping meetings in the calendar for any participant."""
    new_start = _normalize_dt(scheduled_at)
    new_end = new_start + timedelta(minutes=duration_minutes)

    all_meetings, _ = await meeting_repo.list(skip=0, limit=500)
    conflicts: list[MeetingConflict] = []
    user_names: dict[str, str] = {}

    for m in all_meetings:
        if exclude_meeting_id and m.id == exclude_meeting_id:
            continue
        if m.status in (MeetingStatus.CANCELLED, MeetingStatus.REJECTED):
            continue

        m_start = _normalize_dt(m.scheduled_at)
        m_end = m_start + timedelta(minutes=m.duration_minutes)

        # Overlap condition: startA < endB and startB < endA
        if new_start < m_end and m_start < new_end:
            meeting_participants = {m.organiser_id, *m.attendee_ids}
            shared = participant_ids.intersection(meeting_participants)
            if shared:
                shared_names: list[str] = []
                for uid in shared:
                    if user_repo:
                        if uid not in user_names:
                            u = await user_repo.get(uid)
                            user_names[uid] = u.name if u else uid
                        shared_names.append(user_names[uid])
                    else:
                        shared_names.append(uid)

                conflicts.append(MeetingConflict(
                    meeting_id=m.id,
                    title=m.title,
                    scheduled_at=m.scheduled_at,
                    duration_minutes=m.duration_minutes,
                    conflicting_user_ids=list(shared),
                    conflicting_user_names=shared_names,
                ))

    return conflicts


async def _suggest_alternative_slots(
    meeting_repo: Any,
    scheduled_at: datetime,
    duration_minutes: int,
    participant_ids: set[str],
    exclude_meeting_id: Optional[str] = None,
    max_slots: int = 3,
) -> list[datetime]:
    """Suggest alternative non-colliding candidate slots."""
    candidates: list[datetime] = []
    base = _normalize_dt(scheduled_at)

    offsets = [30, 45, 60, 90, 120, 180, 240, 1440, 1440 + 60]
    for m in offsets:
        candidate = base + timedelta(minutes=m)
        conflicts = await _find_conflicts(
            meeting_repo=meeting_repo,
            user_repo=None,
            scheduled_at=candidate,
            duration_minutes=duration_minutes,
            participant_ids=participant_ids,
            exclude_meeting_id=exclude_meeting_id,
        )
        if not conflicts:
            candidates.append(candidate)
            if len(candidates) >= max_slots:
                break
    return candidates


async def _enrich_meeting(meeting: Meeting, user_repo: Any) -> MeetingOut:
    """Populate organizer and attendee human-readable display names."""
    data = meeting.model_dump()
    org = await user_repo.get(meeting.organiser_id)
    data["organiser_name"] = org.name if org else meeting.organiser_id

    attendee_names: dict[str, str] = {}
    for aid in meeting.attendee_ids:
        att = await user_repo.get(aid)
        attendee_names[aid] = att.name if att else aid

    data["attendee_names"] = attendee_names
    return MeetingOut.model_validate(data)


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[MeetingOut], summary="List meetings")
async def list_meetings(
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mine: bool = True,
    all_meetings: bool = False,
) -> PaginatedResponse[MeetingOut]:
    skip = (page - 1) * page_size
    filter_user_id = None if (all_meetings or not mine) else current_user.id
    meetings, total = await meeting_repo.list(
        skip=skip, limit=page_size,
        user_id=filter_user_id,
    )
    items = [await _enrich_meeting(m, user_repo) for m in meetings]
    return PaginatedResponse(
        items=items,
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/check-availability", response_model=CalendarAvailabilityResponse,
             summary="Check calendar API for collisions and available slots")
async def check_availability(
    body: CalendarAvailabilityRequest,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
) -> CalendarAvailabilityResponse:
    participants = {current_user.id, *body.attendee_ids}
    conflicts = await _find_conflicts(
        meeting_repo=meeting_repo,
        user_repo=user_repo,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        participant_ids=participants,
        exclude_meeting_id=body.exclude_meeting_id,
    )
    if conflicts:
        suggested = await _suggest_alternative_slots(
            meeting_repo=meeting_repo,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            participant_ids=participants,
            exclude_meeting_id=body.exclude_meeting_id,
        )
        return CalendarAvailabilityResponse(
            available=False,
            conflicts=conflicts,
            suggested_slots=suggested,
            message=f"Collision detected with {len(conflicts)} scheduled call(s)",
        )
    return CalendarAvailabilityResponse(
        available=True,
        conflicts=[],
        suggested_slots=[],
        message="No calendar collisions detected. All participants are free.",
    )


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED,
             summary="Schedule a meeting with calendar collision check and attendee notifications")
async def create_meeting(
    body: MeetingCreate,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    audit_repo: AuditRepoDep,
    notif_repo: NotifRepoDep,
    user_repo: UserRepoDep,
) -> MeetingOut:
    participants = {current_user.id, *body.attendee_ids}

    # Calendar Collision Check
    if not body.force:
        conflicts = await _find_conflicts(
            meeting_repo=meeting_repo,
            user_repo=user_repo,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            participant_ids=participants,
        )
        if conflicts:
            suggested = await _suggest_alternative_slots(
                meeting_repo=meeting_repo,
                scheduled_at=body.scheduled_at,
                duration_minutes=body.duration_minutes,
                participant_ids=participants,
            )
            conflict_descriptions = [
                f"'{c.title}' at {c.scheduled_at.strftime('%H:%M')} ({', '.join(c.conflicting_user_names)})"
                for c in conflicts
            ]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": f"Calendar Collision Alert: Overlaps with {'; '.join(conflict_descriptions)}",
                    "conflicts": [c.model_dump(mode="json") for c in conflicts],
                    "suggested_slots": [s.isoformat() for s in suggested],
                },
            )

    init_status = MeetingStatus.PENDING if body.attendee_ids else MeetingStatus.CONFIRMED
    init_attendee_status = {uid: "pending" for uid in body.attendee_ids}

    meeting_data = body.model_dump(exclude={"force"})
    meeting = Meeting(
        **meeting_data,
        organiser_id=current_user.id,
        status=init_status,
        attendee_status=init_attendee_status,
    )
    created = await meeting_repo.create(meeting)

    # Notify all attendees
    for attendee_id in body.attendee_ids:
        if attendee_id != current_user.id:
            await notif_repo.create(Notification(
                user_id=attendee_id,
                type=NotificationType.MEETING_INVITATION,
                title=f"Meeting Invitation: {created.title}",
                body=(
                    f"{current_user.name} scheduled '{created.title}' with you for "
                    f"{created.scheduled_at.strftime('%a, %b %d at %H:%M')}. "
                    f"Please accept or decline."
                ),
                link="/app/meetings",
                metadata={
                    "meeting_id": created.id,
                    "organiser_id": current_user.id,
                    "organiser_name": current_user.name,
                    "scheduled_at": created.scheduled_at.isoformat(),
                    "duration_minutes": created.duration_minutes,
                },
            ))

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="meeting",
        resource_id=created.id,
        description=f"Scheduled meeting: {created.title}",
    ))
    return await _enrich_meeting(created, user_repo)


@router.post("/{meeting_id}/rsvp", response_model=MeetingRsvpResponse,
             summary="RSVP (Accept or Reject with proposed time and auto-reschedule)")
async def rsvp_meeting(
    meeting_id: str,
    body: MeetingRsvpRequest,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    notif_repo: NotifRepoDep,
    user_repo: UserRepoDep,
    audit_repo: AuditRepoDep,
) -> MeetingRsvpResponse:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    participants = {meeting.organiser_id, *meeting.attendee_ids}
    if current_user.id not in participants:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not a participant of this meeting")

    action = body.action.lower().strip()
    if action not in ("accept", "reject"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Action must be 'accept' or 'reject'")

    if action == "accept":
        meeting.attendee_status[current_user.id] = "accepted"
        if all(meeting.attendee_status.get(aid) == "accepted" for aid in meeting.attendee_ids):
            meeting.status = MeetingStatus.CONFIRMED
        meeting.updated_at = utcnow()
        updated = await meeting_repo.update(meeting)

        if meeting.organiser_id != current_user.id:
            await notif_repo.create(Notification(
                user_id=meeting.organiser_id,
                type=NotificationType.MEETING_ACCEPTED,
                title=f"Invitation Accepted: {meeting.title}",
                body=f"{current_user.name} accepted your meeting invitation for {meeting.scheduled_at.strftime('%a, %b %d at %H:%M')}.",
                link="/app/meetings",
                metadata={"meeting_id": meeting.id, "attendee_id": current_user.id},
            ))

        await audit_repo.create(AuditRecord(
            actor_id=current_user.id,
            actor_email=current_user.email,
            action=AuditAction.UPDATE,
            resource_type="meeting",
            resource_id=meeting.id,
            description=f"Accepted meeting invitation: {meeting.title}",
        ))
        enriched = await _enrich_meeting(updated, user_repo)
        return MeetingRsvpResponse(
            success=True,
            action="accept",
            meeting=enriched,
            message="Meeting invitation accepted successfully",
            auto_rescheduled=False,
        )

    # action == "reject"
    if not body.rejection_reason or not body.rejection_reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A reason must be mentioned when rejecting a meeting",
        )
    if not body.proposed_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please specify the time when you will be available",
        )

    proposed_time = _normalize_dt(body.proposed_time)

    # Check calendar collisions for proposed time across all participants
    conflicts = await _find_conflicts(
        meeting_repo=meeting_repo,
        user_repo=user_repo,
        scheduled_at=proposed_time,
        duration_minutes=meeting.duration_minutes,
        participant_ids=participants,
        exclude_meeting_id=meeting.id,
    )
    if conflicts:
        suggested = await _suggest_alternative_slots(
            meeting_repo=meeting_repo,
            scheduled_at=proposed_time,
            duration_minutes=meeting.duration_minutes,
            participant_ids=participants,
            exclude_meeting_id=meeting.id,
        )
        conflict_details = [
            f"'{c.title}' at {c.scheduled_at.strftime('%H:%M')} ({', '.join(c.conflicting_user_names)})"
            for c in conflicts
        ]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Proposed time collides with existing call: {'; '.join(conflict_details)}",
                "conflicts": [c.model_dump(mode="json") for c in conflicts],
                "suggested_slots": [s.isoformat() for s in suggested],
            },
        )

    old_time = meeting.scheduled_at
    meeting.scheduled_at = proposed_time
    meeting.status = MeetingStatus.RESCHEDULED
    meeting.attendee_status[current_user.id] = "accepted"
    meeting.rejection_reason = body.rejection_reason.strip()
    meeting.proposed_time = proposed_time
    meeting.rescheduled_by = current_user.id
    meeting.reschedule_history.append({
        "from": old_time.isoformat(),
        "to": proposed_time.isoformat(),
        "reason": body.rejection_reason.strip(),
        "by_id": current_user.id,
        "by_name": current_user.name,
        "at": utcnow().isoformat(),
    })
    meeting.updated_at = utcnow()

    updated = await meeting_repo.update(meeting)

    # Notify organiser and other participants
    notify_recipients = {meeting.organiser_id, *meeting.attendee_ids} - {current_user.id}
    for recipient_id in notify_recipients:
        await notif_repo.create(Notification(
            user_id=recipient_id,
            type=NotificationType.MEETING_RESCHEDULED,
            title=f"Call Auto-Rescheduled: {meeting.title}",
            body=(
                f"{current_user.name} was unavailable ('{body.rejection_reason.strip()}') "
                f"and automatically rescheduled the meeting to {proposed_time.strftime('%a, %b %d at %H:%M')}. "
                f"Calendar verified with 0 collisions."
            ),
            link="/app/meetings",
            metadata={
                "meeting_id": meeting.id,
                "rescheduled_by": current_user.id,
                "rescheduled_by_name": current_user.name,
                "old_time": old_time.isoformat(),
                "new_time": proposed_time.isoformat(),
                "reason": body.rejection_reason.strip(),
            },
        ))

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="meeting",
        resource_id=meeting.id,
        description=f"Auto-rescheduled meeting '{meeting.title}' to {proposed_time.isoformat()} (Reason: {body.rejection_reason})",
    ))

    enriched = await _enrich_meeting(updated, user_repo)
    return MeetingRsvpResponse(
        success=True,
        action="reject",
        meeting=enriched,
        message=f"Meeting was automatically set to {proposed_time.strftime('%a, %b %d at %H:%M')}.",
        auto_rescheduled=True,
    )


@router.get("/{meeting_id}", response_model=MeetingOut, summary="Get meeting")
async def get_meeting(
    meeting_id: str,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
) -> MeetingOut:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return await _enrich_meeting(meeting, user_repo)


@router.patch("/{meeting_id}", response_model=MeetingOut, summary="Update meeting")
async def update_meeting(
    meeting_id: str,
    body: MeetingUpdate,
    current_user: CurrentUser,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
    audit_repo: AuditRepoDep,
) -> MeetingOut:
    meeting = await meeting_repo.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.organiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the organiser may update this meeting")

    # If scheduled_at is changing, check for collisions
    if body.scheduled_at is not None:
        duration = body.duration_minutes or meeting.duration_minutes
        attendees = body.attendee_ids if body.attendee_ids is not None else meeting.attendee_ids
        participants = {meeting.organiser_id, *attendees}
        conflicts = await _find_conflicts(
            meeting_repo=meeting_repo,
            user_repo=user_repo,
            scheduled_at=body.scheduled_at,
            duration_minutes=duration,
            participant_ids=participants,
            exclude_meeting_id=meeting.id,
        )
        if conflicts:
            conflict_descriptions = [
                f"'{c.title}' at {c.scheduled_at.strftime('%H:%M')} ({', '.join(c.conflicting_user_names)})"
                for c in conflicts
            ]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": f"Calendar Collision Alert: Overlaps with {'; '.join(conflict_descriptions)}",
                    "conflicts": [c.model_dump(mode="json") for c in conflicts],
                },
            )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(meeting, field, value)
    meeting.updated_at = utcnow()
    updated = await meeting_repo.update(meeting)
    return await _enrich_meeting(updated, user_repo)


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
