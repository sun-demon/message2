from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class MessageType(str, Enum):
    TEXT = "text"
    EMOJI = "emoji" # pure emoji (large)
    STICKER = "sticker"
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    AUDIO = "audio" # music
    VOICE = "voice"
    FILE = "file"
    LOCATION = "location"
    CONTACT = "contact"
    LINK = "link" # preview link


class LinkPreview(BaseModel):
    """
    Schema for link preview (like in Telegram/WhatsApp).
    """
    url: str = Field(..., description="Original URL")
    title: Optional[str] = Field(None, description="Page title")
    description: Optional[str] = Field(None, description="Page description")
    image_url: Optional[str] = Field(None, description="Preview image URL")
    image_width: Optional[int] = Field(None, description="Image width")
    image_height: Optional[int] = Field(None, description="Image height")
    site_name: Optional[str] = Field(None, description="Name of the site")
    favicon: Optional[str] = Field(None, description="Site favicon URL")


class MediaInfo(BaseModel):
    """Schema for media file information"""
    url: str
    size: int  # in bytes
    mime_type: str
    filename: Optional[str] = None
    
    # For images/videos/GIFs
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail: Optional[str] = None  # preview URL
    
    # For audio/voice
    duration: Optional[int] = None  # in seconds
    
    # For voice messages specifically
    waveform: Optional[List[int]] = None  # audio visualization


class MessageCreate(BaseModel):
    """
    Schema for creating a new message.
    """
    chat_id: int = Field(..., gt=0, description="ID of the chat")
    message_type: MessageType = Field(MessageType.TEXT, description="text, image, video, gif, voice, file, sticker, ...")
    content: Optional[str] = Field(None, max_length=4096, description="Text content or caption")
    reply_to: Optional[int] = Field(None, gt=0, description="ID of message being replied to (must be > 0)")
    
    # For media
    media: Optional[MediaInfo] = None
    # For links
    link_preview: Optional[LinkPreview] = None

    # Security fields
    security_level: str = Field("maximum", description="maximum, medium, minimum")
    encryption_type: str = Field("e2ee", description="e2ee, transport, none")
    
    @model_validator(mode='after')
    def validate_message(self):
        """Validate based on message type"""
        if self.message_type == "text" and not self.content:
            raise ValueError("Text messages must have content")
        return self


class MessageUpdate(BaseModel):
    """
    Schema for updating a message.
    """
    content: Optional[str] = Field(None, max_length=4096, description="New text content")
    media: Optional[MediaInfo] = Field(None, description="New media info")
    
    @model_validator(mode='after')
    def validate_update(self):
        """At least one field must be provided"""
        if not self.content and not self.media:
            raise ValueError("At least one field (content or media) must be provided")
        return self
    

class MessageEntity(BaseModel):
    """Formatting inside text"""
    type: str  # bold, italic, link, mention, hashtag, etc.
    offset: int  # start position in text
    length: int  # length of entity
    url: Optional[str] = None  # for links
    user_id: Optional[int] = None  # for mentions
    

class MessageResponse(BaseModel):
    """
    Schema for message response.
    """
    id: int
    chat_id: int
    sender_id: int
    message_type: MessageType
    content: Optional[str] = None
    entities: List[MessageEntity] = [] # text formatting
    media: Optional[Dict[str, Any]] = None # main media
    media_album: Optional[List[Dict]] = None # for albums (multiple photos)
    link_preview: Optional[Dict] = None # link preview
    created_at: datetime
    updated_at: datetime
    is_edited: bool = False
    is_deleted: bool = False
    reply_to: Optional[int] = None
    reactions: Dict[str, List[int]] = {}
    
    # Security fields
    security_level: str
    encryption_type: str
    
    model_config = ConfigDict(from_attributes=True)


class MessageReaction(BaseModel):
    """
    Schema for adding/removing reactions.
    """
    reaction: str = Field(..., description="Emoji reaction")
    action: str = Field("add", description="add or remove")