"""
Authentication Routes
POST /auth/register
POST /auth/login
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - **name**: Full name (min 2 chars)
    - **email**: Unique email address
    - **password**: Min 6 characters (stored as bcrypt hash)
    - **role**: `user` (default) or `admin`
    """
    user = UserService.register_user(db, request)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.

    Returns a **Bearer JWT token** to use in the Authorization header
    for all protected routes.
    """
    result = UserService.login_user(db, request)
    return result
