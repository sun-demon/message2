# routers/chats.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from database import get_db
from models.chat import Chat
from models.user import User
from auth.utils import get_current_user
from schemas import chat as chat_schemas

router = APIRouter(prefix="/chats", tags=["chats"])


# Helper function to create Saved Messages
def create_saved_messages_chat(db: Session, user: User) -> Chat:
    """
    Create Saved Messages chat for a user.
    Called automatically after user registration.
    """
    saved_chat = Chat(
        name=None,  # Private chat with self has no name
        chat_type="private",
        created_by=user.id
    )
    db.add(saved_chat)
    db.flush()
    
    # Add only the user themselves
    saved_chat.participants.append(user)
    
    db.commit()
    db.refresh(saved_chat)
    return saved_chat


# Chat CRUD endpoints
@router.post("/", response_model=chat_schemas.ChatResponse)
def create_chat(
    chat_data: chat_schemas.ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat.

    - **private**: 0 members = Saved Messages, 1 member = chat with another user
    - **group**: requires name, members optional
    - **channel**: requires name, members optional
    """
    # Validate chat type
    if chat_data.chat_type not in ["private", "group", "channel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat type. Must be 'private', 'group', or 'channel'"
        )
    
    # Filter the ID, removing the non-existent ones and ourselves.
    other_user_ids = []
    invalid_ids = []
    
    for uid in chat_data.member_ids:
        if uid == current_user.id:
            continue  # Skip ourselves (it will be added automatically)
        # Checking if there is a user with this ID.
        user = db.query(User).filter(User.id == uid).first()
        if user:
            other_user_ids.append(uid)
        else:
            invalid_ids.append(uid)

    # If there are incorrect IDs, we return an understandable error.
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users with IDs {invalid_ids} do not exist"
        )

    # Check if chat is Saved Messages
    if chat_data.chat_type == "private" and len(other_user_ids) == 0:
        # Check if already exists
        existing = (
            db.query(Chat)
            .join(Chat.participants)
            .filter(Chat.chat_type == "private", 
                    Chat.participants.any(User.id == current_user.id))
            .group_by(Chat.id)
            .having(func.count(Chat.id) == 1)
            .first()
        )
        if existing:
            db.refresh(existing, ['participants'])
            return {
                "id": existing.id,
                "name": "Saved Messages",
                "chat_type": existing.chat_type,
                "created_by": existing.created_by,
                "created_at": existing.created_at,
                "updated_at": existing.updated_at,
                "member_count": len(existing.participants)
            }
        
        # Create new Saved Messages chat
        new_chat = create_saved_messages_chat(db, current_user)
        return {
            "id": new_chat.id,
            "name": "Saved Messages",
            "chat_type": new_chat.chat_type,
            "created_by": new_chat.created_by,
            "created_at": new_chat.created_at,
            "updated_at": new_chat.updated_at,
            "member_count": len(new_chat.participants)
        }
    
    # Check if person to person chat (p2p)
    if chat_data.chat_type == "private":
        # Private chat with another user: exactly one other member
        if len(other_user_ids) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private chat with another user must have exactly one member ID"
            )

         # Check if p2p chat already exists between these two users
        other_user_id = other_user_ids[0]
        existing_chat = db.query(Chat).join(
            Chat.participants
        ).filter(
            Chat.chat_type == "private",
            Chat.participants.any(User.id == current_user.id),
            Chat.participants.any(User.id == other_user_id)
        ).group_by(Chat.id).having(func.count(User.id) == 2).first()
        
        if existing_chat:
            # Return existing chat instead of creating new one
            return existing_chat
        else:
            chat_name = None
        
    # Check if group chat
    elif chat_data.chat_type == "group":
        # Group chat: name required
        if not chat_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group chat must have a name"
            )
        chat_name = chat_data.name
        
    # Check if channel chat
    else:  # channel
        # Channel: name required
        if not chat_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel must have a name"
            )
        chat_name = chat_data.name
    
    # Verify member IDs exist (if any)
    members = db.query(User).filter(User.id.in_(other_user_ids)).all() if other_user_ids else []
    
    # Create chat
    db_chat = Chat(
        name=chat_name,
        chat_type=chat_data.chat_type,
        created_by=current_user.id
    )
    db.add(db_chat)
    db.flush()
    
    # Add creator as participant (always)
    db_chat.participants.append(current_user)
    
    # Add other members
    for member in members:
        db_chat.participants.append(member)
    
    db.commit()
    db.refresh(db_chat)
    db.refresh(db_chat, ['participants'])
    
    # Return with member count
    return {
        "id": db_chat.id,
        "name": db_chat.name,
        "chat_type": db_chat.chat_type,
        "created_by": db_chat.created_by,
        "created_at": db_chat.created_at,
        "updated_at": db_chat.updated_at,
        "member_count": len(db_chat.participants)
    }


@router.get("/", response_model=List[chat_schemas.ChatResponse])
def get_my_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all chats for the current user.
    """
    chats = db.query(Chat).join(
        Chat.participants
    ).filter(
        User.id == current_user.id
    ).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for chat in chats:
        # Special display name for Saved Messages
        display_name = chat.name
        if chat.chat_type == "private" and len(chat.participants) == 1:
            display_name = "Saved Messages"
        
        result.append({
            "id": chat.id,
            "name": display_name,
            "chat_type": chat.chat_type,
            "created_by": chat.created_by,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "member_count": len(chat.participants)
        })
    
    return result


@router.get("/{chat_id}", response_model=chat_schemas.ChatDetailResponse)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific chat.
    """
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is a member
    if current_user not in chat.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Prepare member list
    members = [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "is_online": user.is_online
        }
        for user in chat.participants
    ]
    
    # Special display name for Saved Messages
    display_name = chat.name
    if chat.chat_type == "private" and len(chat.participants) == 1:
        display_name = "Saved Messages"
    
    return {
        "id": chat.id,
        "name": display_name,
        "chat_type": chat.chat_type,
        "created_by": chat.created_by,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "member_count": len(chat.participants),
        "members": members
    }


@router.post("/{chat_id}/members", response_model=chat_schemas.ChatDetailResponse)
def add_members(
    chat_id: int,
    request: chat_schemas.AddMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add members to a group chat or channel.
    Only the creator can add members.
    """
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is the creator
    if chat.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the chat creator can add members"
        )
    
    # Cannot add members to private chats
    if chat.chat_type == "private":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add members to private chats"
        )
    
    # Get existing member IDs
    existing_ids = [user.id for user in chat.participants]
    
    # Filter out users who are already members
    new_ids = [uid for uid in request.member_ids if uid not in existing_ids]
    
    if not new_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All users are already members"
        )
    
    # Get users to add
    new_members = db.query(User).filter(User.id.in_(new_ids)).all()
    if len(new_members) != len(new_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more user IDs do not exist"
        )
    
    # Add new members
    for member in new_members:
        chat.participants.append(member)
    
    db.commit()
    db.refresh(chat)
    
    # Return updated chat
    members = [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "is_online": user.is_online
        }
        for user in chat.participants
    ]
    
    return {
        "id": chat.id,
        "name": chat.name,
        "chat_type": chat.chat_type,
        "created_by": chat.created_by,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "member_count": len(chat.participants),
        "members": members
    }


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
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is the creator
    if chat.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the chat creator can remove members"
        )
    
    # Cannot remove from private chats
    if chat.chat_type == "private":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove members from private chats"
        )
    
    # Cannot remove the creator
    if user_id == chat.created_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the chat creator"
        )
    
    # Find user to remove
    user_to_remove = db.query(User).filter(User.id == user_id).first()
    if not user_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is a member
    if user_to_remove not in chat.participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this chat"
        )
    
    # Remove user
    chat.participants.remove(user_to_remove)
    db.commit()
    
    return {"message": "Member removed successfully"}
