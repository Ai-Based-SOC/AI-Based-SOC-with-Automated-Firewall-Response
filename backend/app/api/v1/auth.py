"""
Authentication API routes.

Provides login, logout, token refresh, password management, and MFA endpoints.
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from backend.app.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_password,
)
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AuthenticationError, ValidationError
from backend.app.core.rbac import require_admin
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import (
    LoginRequest,
    MessageResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

settings = get_settings()


@router.post("/login", response_model=TokenResponse, summary="User login")
def login(
    request: Request,
    response: Response,
    credentials: Annotated[LoginRequest, Depends()],
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return access/refresh tokens.
    
    Uses OAuth2 password flow for compatibility with standard clients.
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    if not user.is_active:
        raise AuthenticationError("Account is disabled")
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create tokens
    access_token = create_access_token(subject=user.id, email=user.email)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Store refresh token hash
    auth_service.store_refresh_token(user.id, refresh_token)
    
    # Set secure cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login/json", response_model=TokenResponse, summary="User login (JSON)")
def login_json(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user with JSON body and return access/refresh tokens.
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    if not user.is_active:
        raise AuthenticationError("Account is disabled")
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(subject=user.id, email=user.email)
    refresh_token = create_refresh_token(subject=user.id)
    
    auth_service.store_refresh_token(user.id, refresh_token)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(
    request: Request,
    response: Response,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    user = auth_service.verify_refresh_token(refresh_data.refresh_token)
    
    if not user:
        raise AuthenticationError("Invalid or expired refresh token")
    
    if not user.is_active:
        raise AuthenticationError("Account is disabled")
    
    # Create new tokens
    access_token = create_access_token(subject=user.id, email=user.email)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    # Rotate refresh token
    auth_service.rotate_refresh_token(user.id, refresh_data.refresh_token, new_refresh_token)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENV == "prod",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse, summary="User logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Logout user and invalidate refresh token.
    """
    auth_service = AuthService(db)
    auth_service.revoke_refresh_token(current_user.id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return MessageResponse(message="Successfully logged out")


@router.post("/logout/all", response_model=MessageResponse, summary="Logout from all devices")
def logout_all(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Logout user from all devices by revoking all refresh tokens.
    """
    auth_service = AuthService(db)
    auth_service.revoke_all_refresh_tokens(current_user.id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return MessageResponse(message="Successfully logged out from all devices")


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get the currently authenticated user's profile.
    """
    return UserResponse.model_validate(current_user)


@router.post("/password/change", response_model=MessageResponse, summary="Change password")
def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Change the current user's password.
    """
    auth_service = AuthService(db)
    
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise ValidationError("Current password is incorrect")
    
    auth_service.change_password(current_user.id, password_data.new_password)
    
    return MessageResponse(message="Password changed successfully")


@router.post("/password/reset", response_model=MessageResponse, summary="Request password reset")
def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration.
    """
    auth_service = AuthService(db)
    auth_service.request_password_reset(reset_data.email)
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/password/reset/confirm", response_model=MessageResponse, summary="Confirm password reset")
def confirm_password_reset(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Confirm password reset with token.
    """
    auth_service = AuthService(db)
    auth_service.confirm_password_reset(reset_data.token, reset_data.new_password)
    
    return MessageResponse(message="Password has been reset successfully")


@router.post("/mfa/setup", response_model=MFASetupResponse, summary="Setup MFA")
def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFASetupResponse:
    """
    Setup MFA for the current user.
    
    Returns TOTP secret, QR code, and backup codes.
    """
    auth_service = AuthService(db)
    return auth_service.setup_mfa(current_user.id)


@router.post("/mfa/verify", response_model=MessageResponse, summary="Verify MFA")
def verify_mfa(
    mfa_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Verify MFA code and enable MFA for the user.
    """
    auth_service = AuthService(db)
    auth_service.verify_and_enable_mfa(current_user.id, mfa_data.code)
    
    return MessageResponse(message="MFA enabled successfully")


@router.post("/mfa/disable", response_model=MessageResponse, summary="Disable MFA")
def disable_mfa(
    mfa_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Disable MFA for the current user.
    """
    auth_service = AuthService(db)
    auth_service.disable_mfa(current_user.id, mfa_data.code)
    
    return MessageResponse(message="MFA disabled successfully")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register new user")
def register(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user (admin only).
    """
    auth_service = AuthService(db)
    user = auth_service.create_user(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        password=user_data.password,
        roles=user_data.roles,
    )
    
    return UserResponse.model_validate(user)