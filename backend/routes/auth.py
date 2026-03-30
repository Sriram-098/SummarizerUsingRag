"""
Auth Routes — Google OAuth sign-in/sign-up and user info.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User
from backend.auth import verify_google_token, create_jwt, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token from frontend


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str | None


@router.post("/google", response_model=AuthResponse)
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Verify Google OAuth token, create user if new, return JWT.
    """
    # Verify the Google token
    google_user = verify_google_token(body.credential)

    # Find or create user
    user = db.query(User).filter(User.email == google_user["email"]).first()
    if not user:
        user = User(
            email=google_user["email"],
            name=google_user["name"],
            picture=google_user.get("picture", ""),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT
    token = create_jwt(user.id, user.email)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    }


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
