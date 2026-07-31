from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database.postgres import get_db
from backend.models.schema import User, UserRole, UserSchema
from backend.auth.jwt import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, get_current_user
)
from backend.core.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = UserRole.CUSTOMER.value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSchema


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email is already registered."
        )

    valid_roles = [r.value for r in UserRole]
    if payload.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )

    hashed_pw = get_password_hash(payload.password)
    new_user = User(
        email=payload.email,
        role=payload.role,
        password_hash=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("New user registered", user_id=new_user.id, email=new_user.email, role=new_user.role)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "role": user.role}
    )

    logger.info("User logged in successfully", user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.get("/me", response_model=UserSchema)
def get_current_logged_in_user(current_user: User = Depends(get_current_user)):
    return current_user
