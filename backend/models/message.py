import datetime

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

from database import Base
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
    # JSON with additional information (file size, duration, etc.)
    metadata_json = Column(String(500), nullable=True)
    
    # Statuses
    is_read = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    reply_to = Column(Integer, ForeignKey('messages.id'), nullable=True)
    
    # Links
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    
    def __repr__(self):
        return f"<Message {self.id} in chat {self.chat_id}>"
