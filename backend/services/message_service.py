from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, not_

from models.chat import Chat
from models.message import DeletedMessage, Message
from models.user import User
from schemas.message import MessageCreate, MessageUpdate


class MessageService:
    """Service layer for message business logic"""
    
    # Helper methods
    
    @staticmethod
    def _get_chat_with_access_check(db: Session, chat_id: int, user_id: int) -> Chat:
        """Get chat and verify user membership"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError("Chat not found")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user not in chat.participants:
            raise ValueError("You are not a member of this chat")
        
        return chat
    
    @staticmethod
    def _get_message_with_access_check(
        db: Session, 
        message_id: int, 
        user_id: int,
        check_author: bool = False
    ) -> Message:
        """Get message and verify access"""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError("Message not found")
        
        # Check chat membership
        chat = db.query(Chat).filter(Chat.id == message.chat_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if user not in chat.participants:
            raise ValueError("You are not a member of this chat")
        
        # Check if message is deleted for this user
        deleted_for_user = db.query(DeletedMessage).filter(
            DeletedMessage.message_id == message_id,
            DeletedMessage.user_id == user_id
        ).first()
        
        if deleted_for_user:
            raise ValueError("Message was deleted")
        
        # Check author if required
        if check_author and message.sender_id != user_id:
            raise ValueError("You can only edit your own messages")
        
        return message
    
    @staticmethod
    def _validate_reply_to(
        db: Session, 
        reply_to: Optional[int], 
        chat_id: int
    ) -> None:
        """Validate that replied message exists"""
        if not reply_to:
            return
        
        if reply_to <= 0:
            raise ValueError("Invalid reply_to ID. Must be a positive integer.")
        
        reply_msg = db.query(Message).filter(
            and_(
                Message.id == reply_to,
                Message.chat_id == chat_id,
                Message.is_deleted == False
            )
        ).first()
        
        if not reply_msg:
            raise ValueError(f"Message with id {reply_to} not found in this chat")
    
    @staticmethod
    def _update_chat_timestamp(db: Session, chat_id: int) -> None:
        """Update chat's updated_at timestamp"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            chat.updated_at = datetime.now(timezone.utc)
            db.commit()
    
    # Message CRUD
    
    @staticmethod
    def create_message(
        db: Session,
        message_data: MessageCreate,
        sender_id: int
    ) -> Message:
        """
        Create a new message.
        Used by both REST and WebSocket.
        """
        # Check chat access
        MessageService._get_chat_with_access_check(db, message_data.chat_id, sender_id)
        
        # Validate reply_to
        MessageService._validate_reply_to(db, message_data.reply_to, message_data.chat_id)
        
        # Create message
        new_message = Message(
            chat_id=message_data.chat_id,
            sender_id=sender_id,
            content=message_data.content,
            message_type=message_data.message_type.value,
            reply_to=message_data.reply_to,
            security_level=message_data.security_level,
            encryption_type=message_data.encryption_type,
            reactions={}
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update chat timestamp
        MessageService._update_chat_timestamp(db, message_data.chat_id)
        
        return new_message
    
    @staticmethod
    def get_chat_messages(
        db: Session,
        chat_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        before: Optional[int] = None
    ) -> List[Message]:
        """
        Get message history for a chat with pagination.
        """
        # Check chat access
        MessageService._get_chat_with_access_check(db, chat_id, user_id)
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # Build query
        query = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.is_deleted == False
        ).filter(
            not_(Message.deleted_by.any(DeletedMessage.user_id == user_id))
        )
        
        # Apply before filter
        if before:
            before_msg = db.query(Message.created_at).filter(Message.id == before).first()
            if before_msg:
                query = query.filter(Message.created_at < before_msg[0])
        
        # Get messages (newest first)
        messages = query.order_by(
            Message.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Return in chronological order
        messages.reverse()
        
        return messages
    
    @staticmethod
    def get_message(
        db: Session,
        message_id: int,
        user_id: int
    ) -> Message:
        """Get a single message by ID."""
        return MessageService._get_message_with_access_check(db, message_id, user_id)
    
    @staticmethod
    def update_message(
        db: Session,
        message_id: int,
        update_data: MessageUpdate,
        user_id: int
    ) -> Message:
        """Update a message."""
        # Get message with access check (must be author)
        message = MessageService._get_message_with_access_check(
            db, message_id, user_id, check_author=True
        )
        
        # Check if message is globally deleted
        if message.is_deleted:
            raise ValueError("Cannot edit deleted message")
        
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
    
    @staticmethod
    def delete_message(
        db: Session,
        message_id: int,
        user_id: int,
        delete_for_all: bool = False
    ) -> Dict[str, str]:
        """Delete a message (for self or for everyone)."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError("Message not found")
        
        is_author = (message.sender_id == user_id)
        
        # Delete for everyone
        if delete_for_all:
            if not is_author:
                raise ValueError("Only author can delete for all")
            
            if message.is_deleted:
                raise ValueError("Message already deleted")
            
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
                DeletedMessage.user_id == user_id
            ).first()
            
            if already_deleted:
                raise ValueError("Message already deleted for you")
            
            # Add to deleted messages
            deleted = DeletedMessage(
                message_id=message_id,
                user_id=user_id
            )
            db.add(deleted)
            db.commit()
            
            return {"message": "Message deleted for you"}
