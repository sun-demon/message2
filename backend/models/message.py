from datetime import datetime, UTC

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from db.session import Base
from models.base import TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Content
    # 'text', 'image', 'file', 'voice'
    message_type = Column(String(20), nullable=False, default='text')
    # the text of the message or the link to the file
    content = Column(Text, nullable=True)
    
    # Statuses
    is_read = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Metadata
    reply_to = Column(Integer, ForeignKey('messages.id'), nullable=True)
    reactions = Column(JSON, default={})

    # Security fields (for future use)
    security_level = Column(String(20), default="maximum")
    encryption_type = Column(String(20), default="e2ee")
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    deleted_by = relationship("DeletedMessage", backref="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message {self.id} in chat {self.chat_id}>"
    

class DeletedMessage(Base):
    __tablename__ = "deleted_messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    deleted_at = Column(DateTime, default=datetime.now(UTC))
    
    __table_args__ = (UniqueConstraint('message_id', 'user_id', name='unique_message_user_deleted'),)
