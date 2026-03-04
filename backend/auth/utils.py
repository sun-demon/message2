from datetime import datetime, timedelta, timezone
import re
from typing import Optional, Union

from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth.config import SECRET_KEY, ALGORITHM
from models.user import User
from database import get_db

# Setting up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for obtaining a token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_password_hash(password: str) -> str:
    """Hashes the password with truncation to 72 bytes (bcrypt limitation)"""
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks the password, truncating it to 72 bytes if necessary"""
    if isinstance(plain_password, str):
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, login: str, password: str) -> Union[User, bool]:
    """
    User authentication by login (username, phone, or email).
    Returns the user or False.
    """
    user = db.query(User).filter(
        (User.username == login) | 
        (User.phone == login) | 
        (User.email == login)
    ).first()


    # If we haven't found it, and it looks like a phone (numbers only)
    if not user and login.replace('+', '').replace('-', '').replace(' ', '').isdigit():
        # Normalize the number: delete everything except the digits and add +
        digits = re.sub(r'\D', '', login)
        if 10 <= len(digits) <= 15:
            normalized_phone = f'+{digits}'
            user = db.query(User).filter(User.phone == normalized_phone).first()
    
    if not user:
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Gets the current user from the JWT token.
    It is used as a dependency for protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user
