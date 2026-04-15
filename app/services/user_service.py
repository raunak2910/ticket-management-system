"""
User Service - Business Logic Layer
Handles user registration and authentication
"""
import logging
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegisterRequest, UserLoginRequest
from app.auth.jwt_handler import hash_password, verify_password, create_access_token
from app.core.exceptions import EmailAlreadyExistsError, AuthenticationError

logger = logging.getLogger(__name__)


class UserService:

    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> User:
        """
        Register a new user.
        - Checks for duplicate email
        - Hashes the password
        - Saves user to DB
        """
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise EmailAlreadyExistsError(request.email)

        hashed_pw = hash_password(request.password)
        user = User(
            name=request.name,
            email=request.email,
            password=hashed_pw,
            role=request.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user registered: {user.email} (role={user.role})")
        return user

    @staticmethod
    def login_user(db: Session, request: UserLoginRequest) -> dict:
        """
        Authenticate a user and return a JWT token.
        - Verifies email + password
        - Issues access token on success
        """
        user = db.query(User).filter(User.email == request.email).first()

        if not user or not verify_password(request.password, user.password):
            logger.warning(f"Failed login attempt for email: {request.email}")
            raise AuthenticationError("Invalid email or password.")

        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        logger.info(f"User logged in: {user.email}")
        return {"access_token": token, "token_type": "bearer", "user": user}
