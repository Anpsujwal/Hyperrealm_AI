"""
Notifications routes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from ..auth import CurrentUser
from ..dependencies import NotifRepoDep
from ..schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut], summary="My notifications")
async def list_notifications(
    current_user: CurrentUser,
    notif_repo: NotifRepoDep,
    unread_only: bool = False,
) -> list[NotificationOut]:
    items = await notif_repo.list_by_user(current_user.id, unread_only=unread_only)
    return [NotificationOut.model_validate(n.model_dump()) for n in items]


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT,
             response_class=Response, summary="Mark notification as read")
async def mark_read(
    notification_id: str,
    current_user: CurrentUser,
    notif_repo: NotifRepoDep,
) -> Response:
    if not await notif_repo.mark_read(notification_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Notification not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT,
             response_class=Response, summary="Mark all notifications as read")
async def mark_all_read(
    current_user: CurrentUser,
    notif_repo: NotifRepoDep,
) -> Response:
    await notif_repo.mark_all_read(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
