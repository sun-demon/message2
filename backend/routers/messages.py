from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import not_
from sqlalchemy.orm import Session

from auth.utils import get_current_user
from database import get_db
from models.user import User
from models.chat import Chat
from models.message import Message, DeletedMessage
from schemas import message as message_schemas

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=message_schemas.MessageResponse)
def create_message(
    message_data: message_schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a new message to a chat.
    """
    # Check if chat exists
    chat = db.query(Chat).filter(Chat.id == message_data.chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if user is a member of the chat
    if current_user not in chat.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Check if replying to a valid message
    if message_data.reply_to:
        # Check that the ID is positive
        if message_data.reply_to <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reply_to ID. Must be a positive integer."
            )
        
        # Check that the message exists and has not been deleted
        reply_msg = db.query(Message).filter(
            Message.id == message_data.reply_to,
            Message.chat_id == message_data.chat_id,
            Message.is_deleted == False
        ).first()
        
        if not reply_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message with id {message_data.reply_to} not found in this chat"
            )
    else:
        # If reply_to is not specified or None, leave it as it is
        pass
    
    # Create message
    new_message = Message(
        chat_id=message_data.chat_id,
        sender_id=current_user.id,
        content=message_data.content,
        message_type=message_data.message_type,
        reply_to=message_data.reply_to if message_data.reply_to else None,  # If None, the database will be NULL
        security_level=message_data.security_level,
        encryption_type=message_data.encryption_type,
        reactions={}
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Update chat's updated_at timestamp
    from datetime import datetime
    chat.updated_at = datetime.utcnow()
    db.commit()
    
    return new_message

@router.get("/chats/{chat_id}/messages", response_model=List[message_schemas.MessageResponse])
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
    
    - **skip**: number of messages to skip (for offset pagination)
    - **limit**: max number of messages to return (default 50, max 100)
    - **before**: get messages before this message ID (for infinite scroll)
    """
    # Check if chat exists
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
    
    # Validate limit
    if limit > 100:
        limit = 100
    
    # Build query: messages not globally deleted AND not deleted by current user
    query = db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.is_deleted == False
    ).filter(
        not_(Message.deleted_by.any(DeletedMessage.user_id == current_user.id))
    )
    
    # If 'before' is specified, get messages older than that message
    if before:
        # First, get the timestamp of the 'before' message
        before_msg = db.query(Message.created_at).filter(Message.id == before).first()
        if before_msg:
            query = query.filter(Message.created_at < before_msg[0])
    
    # Get messages (newest first for pagination)
    messages = query.order_by(
        Message.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Return in chronological order (oldest first)
    messages.reverse()
    
    return messages


@router.get("/messages/{message_id}", response_model=message_schemas.MessageResponse)
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single message by ID.
    Returns message only if it's not deleted for the current user.
    """
    # Check if message exists and is not globally deleted
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.is_deleted == False
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if user is a member of the chat
    chat = db.query(Chat).filter(Chat.id == message.chat_id).first()
    if current_user not in chat.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    # Check if message is deleted for this user
    deleted_for_user = db.query(DeletedMessage).filter(
        DeletedMessage.message_id == message_id,
        DeletedMessage.user_id == current_user.id
    ).first()
    
    if deleted_for_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message was deleted"
        )
    
    return message


@router.put("/{message_id}", response_model=message_schemas.MessageResponse)
def update_message(
    message_id: int,
    update_data: message_schemas.MessageUpdate,
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
    # Find message (including check for deletion)
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if message is globally deleted
    if message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit deleted message"
        )
    
    # Check if message is deleted for this user
    deleted_for_user = db.query(DeletedMessage).filter(
        DeletedMessage.message_id == message_id,
        DeletedMessage.user_id == current_user.id
    ).first()
    
    if deleted_for_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit message that you deleted"
        )
    
    # Check if user is the author
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )
    
    # Update fields
    updated = False
    if update_data.content is not None:
        message.content = update_data.content
        updated = True
    
    if update_data.media is not None:
        message.media = update_data.media.dict() if update_data.media else None
        updated = True
    
    if updated:
        message.is_edited = True
        db.commit()
        db.refresh(message)
    
    return message


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
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    is_author = (message.sender_id == current_user.id)
    
    # Delete for everyone
    if delete_for_all:
        if not is_author:
            raise HTTPException(status_code=403, detail="Only author can delete for all")
        
        if message.is_deleted:
            raise HTTPException(status_code=400, detail="Message already deleted")
        
        # Update replies
        db.query(Message).filter(Message.reply_to == message_id).update(
            {Message.reply_to: None}
        )
        db.delete(message)
        db.commit()
        return {"message": "Message deleted for everyone"}
    
    # Delete for self
    else:
        # Check if already deleted for this user
        already_deleted = db.query(DeletedMessage).filter(
            DeletedMessage.message_id == message_id,
            DeletedMessage.user_id == current_user.id
        ).first()
        
        if already_deleted:
            raise HTTPException(status_code=400, detail="Message already deleted for you")
        
        # Add to deleted messages
        deleted = DeletedMessage(
            message_id=message_id,
            user_id=current_user.id
        )
        db.add(deleted)
        db.commit()
        
        return {"message": "Message deleted for you"}
