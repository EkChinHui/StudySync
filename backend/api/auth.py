"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
import json

from backend.database import get_db
from backend.models import User
from backend.auth_utils import create_access_token, decode_access_token, get_password_hash, verify_password
from backend.config import get_settings

router = APIRouter()
security = HTTPBearer()
settings = get_settings()


class UserCreate(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user_id: str


class GoogleCalendarConnect(BaseModel):
    """Google Calendar connection model."""
    access_token: str
    refresh_token: str
    token_uri: Optional[str] = "https://oauth2.googleapis.com/token"
    scopes: Optional[list] = ["https://www.googleapis.com/auth/calendar"]


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.id, "email": new_user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }


@router.post("/calendar/connect")
async def connect_calendar(
    calendar_data: GoogleCalendarConnect,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Connect Google Calendar for a user."""
    # Decode token to get user
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Store calendar credentials (in production, encrypt these!)
    calendar_credentials = {
        "token": calendar_data.access_token,
        "refresh_token": calendar_data.refresh_token,
        "token_uri": calendar_data.token_uri,
        "scopes": calendar_data.scopes,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret
    }

    user.google_calendar_token = json.dumps(calendar_credentials)
    user.google_refresh_token = calendar_data.refresh_token

    db.commit()

    return {"message": "Google Calendar connected successfully"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
