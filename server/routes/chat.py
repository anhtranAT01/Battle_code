"""World and match spectator chat API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import ChatMessage, User
from server.routes.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
    """Payload for broadcasting a chat message."""
    content: str = Field(..., min_length=1, max_length=500)
    channel: str = Field(default="world", max_length=32)
    match_id: Optional[int] = None


def _serialize_message(msg: ChatMessage) -> Dict[str, Any]:
    """Format ChatMessage entity into API response dictionary."""
    return {
        "id": msg.id,
        "channel": msg.channel,
        "match_id": msg.match_id,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%H:%M:%S") if msg.created_at else "",
        "user": {
            "id": msg.user.id,
            "username": msg.user.username,
            "avatar": getattr(msg.user, "avatar", "ninja") or "ninja",
            "is_admin": msg.user.is_admin,
            "elo": msg.user.elo,
            "rank_tier": getattr(msg.user, "rank_tier", None),
        } if msg.user else None,
    }


@router.get("/messages", response_model=List[Dict[str, Any]])
def get_chat_messages(
    channel: str = Query("world", description="Chat channel ('world' or 'match')"),
    match_id: Optional[int] = Query(None, description="Match ID for match-specific spectator chat"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieve recent chat messages for world channel or specific match."""
    query = db.query(ChatMessage)
    if channel == "match" and match_id is not None:
        query = query.filter(ChatMessage.channel == "match", ChatMessage.match_id == match_id)
    else:
        query = query.filter(ChatMessage.channel == "world")

    messages = (
        query.order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    # Reverse so oldest in the limit window is first
    messages.reverse()
    return [_serialize_message(m) for m in messages]


@router.post("/send", status_code=status.HTTP_201_CREATED)
def send_chat_message(
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Publish a chat message to world channel or match spectator chat."""
    clean_content = payload.content.strip()
    if not clean_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat message cannot be blank.",
        )

    channel = "match" if (payload.channel == "match" and payload.match_id) else "world"
    match_id = payload.match_id if channel == "match" else None

    msg = ChatMessage(
        user_id=current_user.id,
        channel=channel,
        match_id=match_id,
        content=clean_content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return _serialize_message(msg)
