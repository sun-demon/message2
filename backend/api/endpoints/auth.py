from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core import security
from core.security import create_access_token, get_password_hash, oauth2_scheme
from db.session import get_db
from models.user import User
from services.auth_service import AuthService
from services.chat_service import ChatService
from schemas.auth import Token, UserCreate, UserLogin, UserResponse 

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registration of a new user.
    Supports registration by phone OR email (at least one).
    """
    # Checking if username is busy
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Checking if the phone number is busy (if specified)
    if user_data.phone:
        existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Checking if the email is busy (if specified)
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Hashing the password
    hashed_password = get_password_hash(user_data.password)
    
    # Creating a user
    db_user = User(
        username=user_data.username,
        phone=user_data.phone,
        email=user_data.email,
        hashed_password=hashed_password,
        is_bot=user_data.is_bot,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    ChatService.create_saved_messages_chat(db, db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Log in to the system.
    login can be: username, phone, or email.
    """
    user = AuthService.authenticate_user(db, login_data.login, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Creating a token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Updating last_seen
    user.last_seen = datetime.now(timezone.utc)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


# For backward compatibility (if necessary)
@router.post("/token", response_model=Token, include_in_schema=False)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint.
    Accepts application/x-www-form-urlencoded data.
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    user.last_seen = datetime.now(timezone.utc)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Getting information about the current user.
    """
    user = security.get_current_user(token, db)
    return user
