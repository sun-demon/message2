from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from db.session import get_db
from models.user import User
from schemas.message import MessageCreate, MessageResponse, MessageUpdate
from services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a new message to a chat.
    """
    try:
        return MessageService.create_message(db, message_data, current_user.id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    before: Optional[int] = None
):
    """
    Get message history for a chat with pagination.
    
    - **skip**: number of messages to skip
    - **limit**: max number of messages to return (default 50, max 100)
    - **before**: get messages before this message ID (for infinite scroll)
    """
    try:
        return MessageService.get_chat_messages(
            db, chat_id, current_user.id, skip, limit, before
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single message by ID.
    Returns message only if it's not deleted for the current user.
    """
    try:
        return MessageService.get_message(db, message_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: int,
    update_data: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit your own message.
    
    - Only the author can edit a message
    - Updates `is_edited` flag automatically
    - Can update content and/or media
    - Cannot edit deleted messages
    """
    try:
        return MessageService.update_message(db, message_id, update_data, current_user.id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "only edit your own" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    delete_for_all: bool = False
):
    """
    Delete a message.
    
    - **delete_for_all**: if True and user is author, deletes for everyone
    - If False, marks as deleted only for current user
    """
    try:
        return MessageService.delete_message(db, message_id, current_user.id, delete_for_all)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "Only author" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
