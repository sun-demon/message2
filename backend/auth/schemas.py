from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator, field_serializer


# Schemes for creating a user
class UserCreate(BaseModel):
    """
    The scheme for registering a new user.
    Supports registration by phone OR email (at least one).
    """
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Username (unique, 3-50 characters)"
    )
    password: str = Field(
        ..., 
        min_length=6,
        description="Password (min 6 characters)"
    )
    
    # Contact information (at least one must be provided)
    phone: Optional[str] = Field(
        None, 
        pattern=r'^\+?[0-9]{10,15}$',
        description="Phone number in international format (e.g., +79001234567)"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email address"
    )
    
    # Account type
    is_bot: bool = Field(
        False,
        description="Flag indicating if this is a bot account"
    )
    
    @validator('phone')
    def normalize_phone(cls, v):
        if v is None:
            return v
        
        # Delete everything except the numbers
        digits = re.sub(r'\D', '', v)
        
        if not (10 <= len(digits) <= 15):
            raise ValueError('Phone must contain 10-15 digits')
        
        return f'+{digits}'

    @validator('email', always=True)
    def check_contact(cls, v, values):
        """
        A validator that verifies the presence of at least one contact.
        It is called after all fields.
        """
        # If this is an email call, check the phone from values
        phone = values.get('phone')
        email = v
        
        if not phone and not email:
            raise ValueError('Either phone or email must be provided')
        
        return v


# Schemes for responding with user data
class UserResponse(BaseModel):
    """
    Scheme for returning user data (without a password).
    """
    id: int
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_bot: bool
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Login schemes
class UserLogin(BaseModel):
    """
    The scheme for logging in to the system.
    login can be: username, phone, or email.
    """
    login: str = Field(
        ...,
        description="Username, phone or email"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Password"
    )


# Schemes for JWT tokens
class Token(BaseModel):
    """
    The scheme for the JWT access token.
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        "bearer",
        description="Token type (usually 'bearer')"
    )

    #from_attributes is optional, but we'll leave it for uniformity.
    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """
    The schema for the data stored in the JWT token.
    It is used internally, not for the API.
    """
    username: Optional[str] = None