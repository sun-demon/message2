from datetime import datetime, timedelta, timezone
import re
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core.security import create_access_token, get_password_hash, verify_password
from models.user import User
from schemas.auth import UserCreate
from services.chat_service import ChatService


class AuthService:
    """Service layer for authentication business logic"""
    
    @staticmethod
    def _check_username_unique(db: Session, username: str) -> bool:
        """Check if username is already taken"""
        return db.query(User).filter(User.username == username).first() is not None
    
    @staticmethod
    def _check_phone_unique(db: Session, phone: Optional[str]) -> bool:
        """Check if phone is already registered"""
        if not phone:
            return False
        return db.query(User).filter(User.phone == phone).first() is not None
    
    @staticmethod
    def _check_email_unique(db: Session, email: Optional[str]) -> bool:
        """Check if email is already registered"""
        if not email:
            return False
        return db.query(User).filter(User.email == email).first() is not None
    
    @classmethod
    def register_user(cls, db: Session, user_data: UserCreate) -> User:
        """
        Register a new user with all validations.
        Raises ValueError with appropriate message if validation fails.
        """
        # Check username uniqueness
        if cls._check_username_unique(db, user_data.username):
            raise ValueError("Username already taken")
        
        # Check phone uniqueness (if provided)
        if user_data.phone and cls._check_phone_unique(db, user_data.phone):
            raise ValueError("Phone number already registered")
        
        # Check email uniqueness (if provided)
        if user_data.email and cls._check_email_unique(db, user_data.email):
            raise ValueError("Email already registered")
        
        # Create user
        db_user = User(
            username=user_data.username,
            phone=user_data.phone,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_bot=user_data.is_bot,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create Saved Messages chat for the new user
        ChatService.create_saved_messages(db, db_user)
        
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, login: str, password: str) -> Optional[User]:
        """
        Authenticate user by username, phone, or email.
        Returns User if successful, None otherwise.
        """
        # Try to find user by exact match
        user = db.query(User).filter(
            (User.username == login) | 
            (User.phone == login) | 
            (User.email == login)
        ).first()
        
        # If not found, try to normalize as phone number
        if not user and login.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            digits = re.sub(r'\D', '', login)
            if 10 <= len(digits) <= 15:
                normalized_phone = f'+{digits}'
                user = db.query(User).filter(User.phone == normalized_phone).first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    def create_user_token(user: User) -> Tuple[str, str]:
        """
        Create JWT token for authenticated user.
        Returns (access_token, token_type)
        """
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        return access_token, "bearer"
    
    @staticmethod
    def update_last_seen(db: Session, user: User) -> None:
        """Update user's last_seen timestamp"""
        user.last_seen = datetime.now(timezone.utc)
        db.commit()
