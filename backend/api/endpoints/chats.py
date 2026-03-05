from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_current_user
from db.session import get_db
from models.user import User
from services.chat_service import ChatService
from schemas.chat import AddMembersRequest, ChatCreate, ChatDetailResponse, ChatResponse

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
def create_chat(
    chat_data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat.

    - **private**: 0 members = Saved Messages, 1 member = chat with another user
    - **group**: requires name, members optional
    - **channel**: requires name, members optional
    """
    try:
        return ChatService.create_chat(db, chat_data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ChatResponse])
def get_my_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all chats for the current user.
    """
    return ChatService.get_user_chats(db, current_user.id, skip, limit)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific chat.
    """
    try:
        return ChatService.get_chat_details(db, chat_id, current_user.id)
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


@router.post("/{chat_id}/members", response_model=ChatDetailResponse)
def add_members(
    chat_id: int,
    request: AddMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add members to a group chat or channel.
    Only the creator can add members.
    """
    try:
        return ChatService.add_members(db, chat_id, request.member_ids, current_user.id)
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


@router.delete("/{chat_id}/members/{user_id}")
def remove_member(
    chat_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a member from a group chat or channel.
    Only the creator can remove members.
    """
    try:
        return ChatService.remove_member(db, chat_id, user_id, current_user.id)
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