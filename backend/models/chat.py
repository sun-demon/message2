from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime, func
from sqlalchemy.orm import relationship

from database import Base
from models.base import TimestampMixin

# Many-to-many participants (intermediate table for chat participants)
chat_participants = Table(
    'chat_participants',
    Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, server_default=func.now()),
)


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # null for personal chats
    chat_type = Column(String(20), nullable=False)  # 'private', 'group', 'channel'
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Links
    creator = relationship("User", foreign_keys=[created_by])
    participants = relationship("User", secondary=chat_participants, lazy="joined")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat {self.id} ({self.chat_type})>"
