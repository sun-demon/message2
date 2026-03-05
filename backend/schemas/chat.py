from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatBase(BaseModel):
    """Base chat schema"""
    name: Optional[str] = Field(None, description="Chat name (null for private chats)")
    chat_type: str = Field(..., description="private, group, or channel")


class ChatCreate(ChatBase):
    """Schema for creating a new chat"""
    member_ids: List[int] = Field(
        default=[], 
        description="User IDs to add to chat (don't include yourself)"
    )
    
    @classmethod
    def validate_chat(cls, values):
        """Custom validation for different chat types"""
        chat_type = values.get('chat_type')
        member_ids = values.get('member_ids', [])
        name = values.get('name')
        
        if chat_type == "private":
            if len(member_ids) > 1:
                raise ValueError("Private chat must have 0 or 1 other member")
            # Name is ignored for private chats
        
        elif chat_type == "group":
            if not name:
                raise ValueError("Group chat must have a name")
            # Members can be added later, so no minimum required
        
        elif chat_type == "channel":
            if not name:
                raise ValueError("Channel must have a name")
            # Members can be added later
        
        return values


class ChatResponse(BaseModel):
    """Schema for chat response (list view)"""
    id: int
    name: Optional[str] = None
    chat_type: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ChatDetailResponse(ChatResponse):
    """Schema for detailed chat info (with members)"""
    members: List[dict] = Field(default=[], description="List of chat members")
    
    model_config = ConfigDict(from_attributes=True)


class ChatMemberResponse(BaseModel):
    """Schema for chat member info"""
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool
    
    model_config = ConfigDict(from_attributes=True)


class AddMembersRequest(BaseModel):
    """Schema for adding members to a chat"""
    member_ids: List[int] = Field(..., description="User IDs to add")
