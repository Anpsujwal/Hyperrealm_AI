"""
Meetings routes with Calendar Collision Detection, RSVP Notifications, and Automatic Rescheduling.
"""
from __future__ import annotations
from PIL.Image import logger


from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser
from ..dependencies import AuditRepoDep, MeetingRepoDep, NotifRepoDep, ProposalRepoDep, UserRepoDep
from ..models import (
    AuditAction,
    AuditRecord,
    Meeting,
    MeetingProposal,
    MeetingStatus,
    MeetingType,
    Notification,
    NotificationType,
    new_id,
    utcnow,
)
from ..schemas import (
    CalendarAvailabilityRequest,
    CalendarAvailabilityResponse,
    MeetingConflict,
    MeetingCreate,
    MeetingOut,
    MeetingProposalConfirm,
    MeetingProposalCreate,
    MeetingProposalOut,
    MeetingProposalUpdate,
    MeetingRsvpRequest,
    MeetingRsvpResponse,
    MeetingUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


# ─── Calendar Collision & Availability Helpers ─────────────────────────────────

IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def _to_ist_dt(dt: datetime) -> datetime:
    """Convert any naive or aware datetime into timezone-aware IST."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def _to_ist_str(dt: datetime) -> str:
    """Format into readable 12-hour IST time e.g. '06:00 PM IST'."""
    return _to_ist_dt(dt).strftime("%I:%M %p IST")


def _to_ist_full_str(dt: datetime) -> str:
    """Format into full date and time in IST e.g. 'Sun, Oct 18 at 06:00 PM IST'."""
    return _to_ist_dt(dt).strftime("%a, %b %d at %I:%M %p IST")


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
                    scheduled_at=_to_ist_dt(m.scheduled_at),
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
    max_slots: int = 4,
) -> list[datetime]:
    """Suggest alternative non-colliding candidate slots strictly in the future (IST)."""
    candidates: list[datetime] = []
    base = _normalize_dt(scheduled_at)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # Ensure search begins from base or now_utc (whichever is later) to never suggest past slots
    start_point = max(base, now_utc)

    offsets = [30, 45, 60, 90, 120, 180, 240, 300, 360, 1440, 1440 + 60]
    for m in offsets:
        candidate_naive = start_point + timedelta(minutes=m)
        if candidate_naive <= now_utc + timedelta(minutes=2):
            continue
        conflicts = await _find_conflicts(
            meeting_repo=meeting_repo,
            user_repo=None,
            scheduled_at=candidate_naive,
            duration_minutes=duration_minutes,
            participant_ids=participant_ids,
            exclude_meeting_id=exclude_meeting_id,
        )
        if not conflicts:
            candidate_ist = candidate_naive.replace(tzinfo=timezone.utc).astimezone(IST)
            candidates.append(candidate_ist)
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
    force: bool = Query(False),
) -> MeetingOut:
    participants = {current_user.id, *body.attendee_ids}

    # Calendar Collision Check
    if not (force or body.force):
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
                f"'{c.title}' at {_to_ist_str(c.scheduled_at)} ({', '.join(c.conflicting_user_names)})"
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

    # Real Google Calendar / Google Meet integration
    from ..services.calendar_service import get_calendar_service, CalendarError
    calendar_service = get_calendar_service()
    meet_link = None
    google_event_id = None
    cal_provider = "local"

    if calendar_service.is_enabled and hasattr(current_user, "oauth_tokens") and current_user.oauth_tokens.get("google_calendar"):
        try:
            attendee_emails = []
            for aid in body.attendee_ids:
                u = await user_repo.get(aid)
                if u and u.email:
                    attendee_emails.append(u.email)
            
            cal_result = await calendar_service.create_event_with_meet(
                user=current_user,
                title=body.title,
                description=body.description or f"Scheduled via HYPERREALM by {current_user.name}",
                start_time=body.scheduled_at,
                duration_minutes=body.duration_minutes,
                attendee_emails=attendee_emails,
            )
            if cal_result.get("is_live"):
                cal_provider = "google_calendar"
                google_event_id = cal_result.get("event_id")
                meet_link = cal_result.get("meet_link")
        except CalendarError as c_err:
            logger.warning("Google Calendar event creation failed: %s; falling back to internal schedule.", c_err)

    meeting_data = body.model_dump(exclude={"force", "location"})
    meeting = Meeting(
        **meeting_data,
        organiser_id=current_user.id,
        status=init_status,
        attendee_status=init_attendee_status,
        meet_link=meet_link,
        google_event_id=google_event_id,
        calendar_provider=cal_provider,
        location=meet_link or body.location or "Virtual",
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
                    f"{_to_ist_full_str(created.scheduled_at)}. "
                    + (f"Google Meet Link: {meet_link}. " if meet_link else "")
                    + "Please accept or decline."
                ),
                link="/app/meetings",
                metadata={
                    "meeting_id": created.id,
                    "organiser_id": current_user.id,
                    "organiser_name": current_user.name,
                    "scheduled_at": created.scheduled_at.isoformat(),
                    "duration_minutes": created.duration_minutes,
                    "meet_link": meet_link,
                },
            ))

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="meeting",
        resource_id=created.id,
        description=f"Scheduled meeting: {created.title} (provider: {cal_provider})",
    ))
    return await _enrich_meeting(created, user_repo)


# ─── Calendar OAuth Endpoints ─────────────────────────────────────────────────

@router.get("/calendar/status", summary="Get Google Calendar connection status")
async def get_calendar_connection_status(current_user: CurrentUser):
    from ..services.calendar_service import get_calendar_service
    cal_service = get_calendar_service()
    has_token = bool(
        hasattr(current_user, "oauth_tokens")
        and current_user.oauth_tokens
        and current_user.oauth_tokens.get("google_calendar")
    )
    return {
        "integration_enabled": cal_service.is_enabled,
        "is_connected": has_token,
        "provider": "google_calendar" if (cal_service.is_enabled and has_token) else "local",
    }


@router.get("/calendar/auth-url", summary="Get Google OAuth authorization URL")
async def get_calendar_auth_url(current_user: CurrentUser):
    from ..services.calendar_service import get_calendar_service, CalendarError
    cal_service = get_calendar_service()
    if not cal_service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration is not enabled or OAuth credentials missing in configuration.",
        )
    try:
        url = cal_service.get_authorization_url(current_user.id)
        return {"authorization_url": url}
    except CalendarError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/calendar/disconnect", summary="Disconnect Google Calendar OAuth")
async def disconnect_calendar(
    current_user: CurrentUser,
    user_repo: UserRepoDep,
    audit_repo: AuditRepoDep,
):
    if hasattr(current_user, "oauth_tokens") and current_user.oauth_tokens:
        current_user.oauth_tokens.pop("google_calendar", None)
        await user_repo.update(current_user)
        await audit_repo.create(AuditRecord(
            actor_id=current_user.id,
            actor_email=current_user.email,
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=current_user.id,
            description="Disconnected Google Calendar OAuth",
        ))
    return {"status": "disconnected"}


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
                body=f"{current_user.name} accepted your meeting invitation for {_to_ist_full_str(meeting.scheduled_at)}.",
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
            f"'{c.title}' at {_to_ist_str(c.scheduled_at)} ({', '.join(c.conflicting_user_names)})"
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
                f"and automatically rescheduled the meeting to {_to_ist_full_str(proposed_time)}. "
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
        message=f"Meeting was automatically set to {_to_ist_full_str(proposed_time)}.",
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
                f"'{c.title}' at {_to_ist_str(c.scheduled_at)} ({', '.join(c.conflicting_user_names)})"
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


# ─── Meeting Proposals & Confirmation Endpoints ────────────────────────────────

def _enrich_proposal(prop: MeetingProposal) -> MeetingProposalOut:
    return MeetingProposalOut(
        id=prop.id,
        user_id=prop.user_id,
        user_name=prop.user_name,
        user_email=prop.user_email,
        target_user_id=prop.target_user_id,
        target_name=prop.target_name,
        target_email=prop.target_email,
        target_role=prop.target_role,
        title=prop.title,
        description=prop.description,
        scheduled_at=prop.scheduled_at,
        scheduled_at_ist=_to_ist_full_str(prop.scheduled_at),
        duration_minutes=prop.duration_minutes,
        timezone=prop.timezone,
        calendar_status=prop.calendar_status,
        availability_checked=prop.availability_checked,
        availability_note=prop.availability_note,
        status=prop.status,
        meeting_id=prop.meeting_id,
        meet_link=prop.meet_link,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


@router.post("/proposals", response_model=MeetingProposalOut, status_code=status.HTTP_201_CREATED,
             summary="Create or save a pending meeting proposal without scheduling it")
async def create_meeting_proposal(
    body: MeetingProposalCreate,
    current_user: CurrentUser,
    proposal_repo: ProposalRepoDep,
    user_repo: UserRepoDep,
    meeting_repo: MeetingRepoDep,
) -> MeetingProposalOut:
    target_user = await user_repo.get(body.target_user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target participant not found.")

    participants = {current_user.id, target_user.id}
    conflicts = await _find_conflicts(
        meeting_repo=meeting_repo,
        user_repo=user_repo,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        participant_ids=participants,
    )
    if conflicts:
        avail_note = f"Warning: Overlaps with '{conflicts[0].title}'. Consider choosing another slot."
    else:
        avail_note = "Availability verified: No calendar collisions detected for all participants."

    from ..services.calendar_service import get_calendar_service
    cal_svc = get_calendar_service()
    has_cal = bool(cal_svc.is_enabled and hasattr(current_user, "oauth_tokens") and current_user.oauth_tokens.get("google_calendar"))
    cal_status = "Google Calendar Connected (Google Meet video conferencing will be generated upon confirmation)" if has_cal else "Local simulation mode (No external Google account linked)"

    target_role = "Manager" if getattr(current_user, "manager_id", None) == target_user.id else (target_user.job_title or "Subject-Matter Expert")

    proposal = MeetingProposal(
        id=new_id("prop_"),
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        target_user_id=target_user.id,
        target_name=target_user.name,
        target_email=target_user.email,
        target_role=target_role,
        title=body.title,
        description=body.description,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        timezone="IST (UTC+05:30)",
        calendar_status=cal_status,
        availability_checked=True,
        availability_note=avail_note,
        status="pending_confirmation",
    )
    created = await proposal_repo.create(proposal)
    return _enrich_proposal(created)


@router.get("/proposals/{proposal_id}", response_model=MeetingProposalOut,
            summary="Get details of a meeting proposal")
async def get_meeting_proposal(
    proposal_id: str,
    current_user: CurrentUser,
    proposal_repo: ProposalRepoDep,
) -> MeetingProposalOut:
    proposal = await proposal_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found.")
    if proposal.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this proposal.")
    return _enrich_proposal(proposal)


@router.patch("/proposals/{proposal_id}", response_model=MeetingProposalOut,
              summary="Choose Another Time: update and revalidate proposal before confirmation")
async def update_meeting_proposal(
    proposal_id: str,
    body: MeetingProposalUpdate,
    current_user: CurrentUser,
    proposal_repo: ProposalRepoDep,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
) -> MeetingProposalOut:
    proposal = await proposal_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found.")
    if proposal.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this proposal.")
    if proposal.status != "pending_confirmation":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cannot edit proposal in '{proposal.status}' state.")

    if body.scheduled_at is not None:
        proposal.scheduled_at = body.scheduled_at
    if body.duration_minutes is not None:
        proposal.duration_minutes = body.duration_minutes
    if body.title is not None:
        proposal.title = body.title
    if body.description is not None:
        proposal.description = body.description

    participants = {current_user.id, proposal.target_user_id}
    conflicts = await _find_conflicts(
        meeting_repo=meeting_repo,
        user_repo=user_repo,
        scheduled_at=proposal.scheduled_at,
        duration_minutes=proposal.duration_minutes,
        participant_ids=participants,
    )
    if conflicts:
        conflict_desc = [f"'{c.title}' at {_to_ist_str(c.scheduled_at)}" for c in conflicts]
        proposal.availability_checked = True
        proposal.availability_note = f"⚠️ Warning: Overlaps with {'; '.join(conflict_desc)}. Consider an alternate slot."
    else:
        proposal.availability_checked = True
        proposal.availability_note = "✅ Availability verified: No calendar collisions detected for all participants."

    proposal.updated_at = utcnow()
    updated = await proposal_repo.update(proposal)
    return _enrich_proposal(updated)


@router.post("/proposals/{proposal_id}/confirm", summary="Confirm & Schedule meeting proposal")
async def confirm_meeting_proposal(
    proposal_id: str,
    current_user: CurrentUser,
    proposal_repo: ProposalRepoDep,
    meeting_repo: MeetingRepoDep,
    user_repo: UserRepoDep,
    notif_repo: NotifRepoDep,
    audit_repo: AuditRepoDep,
    body: Optional[MeetingProposalConfirm] = None,
) -> dict[str, Any]:
    proposal = await proposal_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found.")
    if proposal.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this meeting proposal.")
    if proposal.status == "confirmed":
        # Duplicate click protection: return existing confirmed meeting if already executed
        if proposal.meeting_id:
            existing = await meeting_repo.get(proposal.meeting_id)
            if existing:
                enriched_m = await _enrich_meeting(existing, user_repo)
                return {
                    "success": True,
                    "already_scheduled": True,
                    "meeting": enriched_m,
                    "proposal": _enrich_proposal(proposal),
                    "message": "Meeting was already confirmed and scheduled.",
                }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal has already been confirmed.")
    if proposal.status in ("cancelled", "expired"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Proposal is {proposal.status} and cannot be confirmed.")

    target_user = await user_repo.get(proposal.target_user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target participant not found in employee directory.")

    # Recheck calendar availability
    participants = {current_user.id, target_user.id}
    conflicts = await _find_conflicts(
        meeting_repo=meeting_repo,
        user_repo=user_repo,
        scheduled_at=proposal.scheduled_at,
        duration_minutes=proposal.duration_minutes,
        participant_ids=participants,
    )
    if conflicts:
        suggested = await _suggest_alternative_slots(
            meeting_repo=meeting_repo,
            scheduled_at=proposal.scheduled_at,
            duration_minutes=proposal.duration_minutes,
            participant_ids=participants,
        )
        conflict_desc = [f"'{c.title}' at {_to_ist_str(c.scheduled_at)}" for c in conflicts]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Proposed time is no longer available due to a collision with: {'; '.join(conflict_desc)}. Please choose another time.",
                "conflicts": [c.model_dump(mode="json") for c in conflicts],
                "suggested_slots": [s.isoformat() for s in suggested],
            },
        )

    # Google Calendar & Meet integration
    from ..services.calendar_service import get_calendar_service, CalendarError
    cal_svc = get_calendar_service()
    cal_provider = "local"
    google_event_id = None
    meet_link = None

    if cal_svc.is_enabled and hasattr(current_user, "oauth_tokens") and current_user.oauth_tokens.get("google_calendar"):
        try:
            attendee_emails = [current_user.email]
            if target_user.email:
                attendee_emails.append(target_user.email)
            cal_result = await cal_svc.create_event_with_meet(
                user=current_user,
                title=proposal.title,
                description=proposal.description or f"Facilitated by HYPERREALM AI for {current_user.name} and {target_user.name}",
                start_time=proposal.scheduled_at,
                duration_minutes=proposal.duration_minutes,
                attendee_emails=attendee_emails,
            )
            if cal_result.get("is_live"):
                cal_provider = "google_calendar"
                google_event_id = cal_result.get("event_id")
                meet_link = cal_result.get("meet_link")
        except CalendarError as c_err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Calendar integration failed: {c_err}. The meeting proposal remains unscheduled so you can retry or choose another time."
            )

    # Create meeting record in meeting_repo
    meeting = Meeting(
        id=new_id("meet_"),
        title=proposal.title,
        type=MeetingType.GENERAL,
        description=proposal.description or f"Scheduled via HYPERREALM for {current_user.name} and {target_user.name}",
        organiser_id=current_user.id,
        attendee_ids=[target_user.id],
        scheduled_at=proposal.scheduled_at,
        duration_minutes=proposal.duration_minutes,
        location=meet_link or "Virtual",
        meet_link=meet_link,
        google_event_id=google_event_id,
        calendar_provider=cal_provider,
        status=MeetingStatus.CONFIRMED,
        attendee_status={target_user.id: "pending"},
    )
    created_meeting = await meeting_repo.create(meeting)

    # Update proposal record
    proposal.status = "confirmed"
    proposal.meeting_id = created_meeting.id
    proposal.meet_link = meet_link
    proposal.updated_at = utcnow()
    await proposal_repo.update(proposal)

    # Notify attendee
    await notif_repo.create(Notification(
        user_id=target_user.id,
        type=NotificationType.MEETING_INVITATION,
        title=f"Meeting Scheduled: {created_meeting.title}",
        body=(
            f"{current_user.name} confirmed and scheduled '{created_meeting.title}' with you for "
            f"{_to_ist_full_str(created_meeting.scheduled_at)}. "
            + (f"Google Meet Link: {meet_link}. " if meet_link else "")
        ),
        link="/app/meetings",
        metadata={
            "meeting_id": created_meeting.id,
            "proposal_id": proposal.id,
            "meet_link": meet_link,
        },
    ))

    # Audit log
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="meeting",
        resource_id=created_meeting.id,
        description=f"Confirmed proposal {proposal.id} and scheduled meeting: {created_meeting.title}",
    ))

    enriched_meeting = await _enrich_meeting(created_meeting, user_repo)
    return {
        "success": True,
        "meeting": enriched_meeting,
        "proposal": _enrich_proposal(proposal),
        "message": "Meeting successfully confirmed and scheduled!",
    }


@router.post("/proposals/{proposal_id}/cancel", response_model=MeetingProposalOut,
             summary="Cancel a meeting proposal")
async def cancel_meeting_proposal(
    proposal_id: str,
    current_user: CurrentUser,
    proposal_repo: ProposalRepoDep,
) -> MeetingProposalOut:
    proposal = await proposal_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting proposal not found.")
    if proposal.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this proposal.")
    proposal.status = "cancelled"
    proposal.updated_at = utcnow()
    updated = await proposal_repo.update(proposal)
    return _enrich_proposal(updated)
