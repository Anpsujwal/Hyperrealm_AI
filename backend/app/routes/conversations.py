"""
Conversation and message persistence routes.

Each conversation belongs to the authenticated user.
Messages are appended to a conversation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from ..auth import CurrentUser
from ..dependencies import ConvRepoDep
from ..models import Conversation, Message, utcnow
from ..schemas import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    PaginatedResponse,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=PaginatedResponse[ConversationOut], summary="List my conversations")
async def list_conversations(
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ConversationOut]:
    skip = (page - 1) * page_size
    convs, total = await conv_repo.list_by_user(
        current_user.id, skip=skip, limit=page_size
    )
    return PaginatedResponse(
        items=[ConversationOut.model_validate(c.model_dump()) for c in convs],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED,
             summary="Create a new conversation")
async def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
) -> ConversationOut:
    conv = Conversation(
        user_id=current_user.id,
        title=body.title,
        agent_id=body.agent_id,
    )
    created = await conv_repo.create(conv)
    return ConversationOut.model_validate(created.model_dump())


@router.get("/{conv_id}", response_model=ConversationOut, summary="Get a conversation")
async def get_conversation(
    conv_id: str,
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
) -> ConversationOut:
    conv = await conv_repo.get(conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied")
    return ConversationOut.model_validate(conv.model_dump())


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete a conversation")
async def delete_conversation(
    conv_id: str,
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
) -> Response:
    conv = await conv_repo.get(conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied")
    await conv_repo.delete(conv_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conv_id}/messages", response_model=PaginatedResponse[MessageOut],
            summary="List messages in a conversation")
async def list_messages(
    conv_id: str,
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
) -> PaginatedResponse[MessageOut]:
    conv = await conv_repo.get(conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied")
    skip = (page - 1) * page_size
    msgs, total = await conv_repo.list_messages(conv_id, skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[MessageOut.model_validate(m.model_dump()) for m in msgs],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/{conv_id}/messages", response_model=MessageOut,
             status_code=status.HTTP_201_CREATED, summary="Add a message")
async def add_message(
    conv_id: str,
    body: MessageCreate,
    current_user: CurrentUser,
    conv_repo: ConvRepoDep,
) -> MessageOut:
    conv = await conv_repo.get(conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied")

    msg = Message(
        conversation_id=conv_id,
        role=body.role,
        content=body.content,
        agent_id=body.agent_id,
        metadata=body.metadata,
    )
    created = await conv_repo.add_message(msg)
    return MessageOut.model_validate(created.model_dump())
