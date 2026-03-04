import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from database import Base
from models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Contact information (at least one must be filled in)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)

    # User name (required)
    username = Column(String(50), unique=True, index=True, nullable=False)

    # You can create a separate field for bots
    is_bot = Column(Boolean, default=False)

    hashed_password = Column(String(200), nullable=False)
    
    # Profile
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    chats = relationship("Chat", secondary="chat_participants", back_populates="participants")
    # If the "Contact" model is implemented
    # contacts = relationship("Contact", foreign_keys="Contact.user_id", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"
