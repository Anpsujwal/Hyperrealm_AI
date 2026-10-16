"""
Incidents routes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..auth import CurrentUser
from ..dependencies import AuditRepoDep, IncidentRepoDep, NotifRepoDep
from ..models import AuditAction, AuditRecord, Incident, Notification, NotificationType, utcnow
from ..schemas import (
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=PaginatedResponse[IncidentOut], summary="List incidents")
async def list_incidents(
    current_user: CurrentUser,
    incident_repo: IncidentRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[IncidentOut]:
    skip = (page - 1) * page_size
    incidents, total = await incident_repo.list(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[IncidentOut.model_validate(i.model_dump()) for i in incidents],
        total=total, page=page, page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED,
             summary="Report an incident")
async def create_incident(
    body: IncidentCreate,
    current_user: CurrentUser,
    incident_repo: IncidentRepoDep,
    notif_repo: NotifRepoDep,
    audit_repo: AuditRepoDep,
) -> IncidentOut:
    incident = Incident(**body.model_dump(), reporter_id=current_user.id)
    created = await incident_repo.create(incident)

    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.CREATE,
        resource_type="incident",
        resource_id=created.id,
        description=f"Reported {created.severity.value} incident: {created.title}",
    ))
    return IncidentOut.model_validate(created.model_dump())


@router.get("/{incident_id}", response_model=IncidentOut, summary="Get incident")
async def get_incident(
    incident_id: str,
    current_user: CurrentUser,
    incident_repo: IncidentRepoDep,
) -> IncidentOut:
    incident = await incident_repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentOut.model_validate(incident.model_dump())


@router.patch("/{incident_id}", response_model=IncidentOut, summary="Update incident")
async def update_incident(
    incident_id: str,
    body: IncidentUpdate,
    current_user: CurrentUser,
    incident_repo: IncidentRepoDep,
    audit_repo: AuditRepoDep,
) -> IncidentOut:
    incident = await incident_repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    from ..models import IncidentStatus
    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(incident, field, value)
    incident.updated_at = utcnow()
    if body.status == IncidentStatus.RESOLVED and not incident.resolved_at:
        incident.resolved_at = utcnow()

    updated = await incident_repo.update(incident)
    await audit_repo.create(AuditRecord(
        actor_id=current_user.id,
        actor_email=current_user.email,
        action=AuditAction.UPDATE,
        resource_type="incident",
        resource_id=incident_id,
        description=f"Updated incident: {updated.title}",
        metadata=updates,
    ))
    return IncidentOut.model_validate(updated.model_dump())
