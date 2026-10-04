"""
User management API routes.

Provides CRUD operations for users, roles, and permissions.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_admin, require_permission
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Users"])

settings = get_settings()


@router.get("", response_model=PaginatedResponse[UserResponse], summary="List users")
def list_users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    current_user: User = Depends(require_permission("users:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    """
    List users with pagination, search, and filtering.
    """
    auth_service = AuthService(db)
    users, total = auth_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
    )
    
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(
    user_id: int,
    current_user: User = Depends(require_permission("users:read")),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get a user by ID.
    """
    auth_service = AuthService(db)
    user = auth_service.get_user(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create user")
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create a new user (admin only).
    """
    auth_service = AuthService(db)
    
    # Check if email already exists
    if auth_service.get_user_by_email(user_data.email):
        raise ValidationError("Email already registered")
    
    # Check if username already exists
    if auth_service.get_user_by_username(user_data.username):
        raise ValidationError("Username already taken")
    
    user = auth_service.create_user(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        password=user_data.password,
        roles=user_data.roles,
    )
    
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update a user (admin only).
    """
    auth_service = AuthService(db)
    user = auth_service.get_user(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    # Prevent self-demotion
    if user_id == current_user.id and user_data.is_active is False:
        raise ValidationError("Cannot deactivate your own account")
    
    updated_user = auth_service.update_user(user_id, user_data)
    
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", response_model=MessageResponse, summary="Delete user")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a user (admin only).
    """
    if user_id == current_user.id:
        raise ValidationError("Cannot delete your own account")
    
    auth_service = AuthService(db)
    auth_service.delete_user(user_id)
    
    return MessageResponse(message="User deleted successfully")


@router.post("/{user_id}/activate", response_model=MessageResponse, summary="Activate user")
def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Activate a user account (admin only).
    """
    auth_service = AuthService(db)
    auth_service.activate_user(user_id)
    
    return MessageResponse(message="User activated successfully")


@router.post("/{user_id}/deactivate", response_model=MessageResponse, summary="Deactivate user")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Deactivate a user account (admin only).
    """
    if user_id == current_user.id:
        raise ValidationError("Cannot deactivate your own account")
    
    auth_service = AuthService(db)
    auth_service.deactivate_user(user_id)
    
    return MessageResponse(message="User deactivated successfully")


@router.post("/{user_id}/roles", response_model=UserResponse, summary="Assign roles to user")
def assign_roles(
    user_id: int,
    role_names: list[str],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Assign roles to a user (admin only).
    """
    auth_service = AuthService(db)
    user = auth_service.assign_roles(user_id, role_names)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}/roles/{role_name}", response_model=UserResponse, summary="Remove role from user")
def remove_role(
    user_id: int,
    role_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Remove a role from a user (admin only).
    """
    auth_service = AuthService(db)
    user = auth_service.remove_role(user_id, role_name)
    
    return UserResponse.model_validate(user)


# =========================================================
# Roles
# =========================================================

@router.get("/roles", response_model=list[RoleResponse], summary="List all roles")
def list_roles(
    current_user: User = Depends(require_permission("roles:read")),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    """
    List all roles.
    """
    auth_service = AuthService(db)
    roles = auth_service.list_roles()
    
    return [RoleResponse.model_validate(r) for r in roles]


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="Get role by ID")
def get_role(
    role_id: int,
    current_user: User = Depends(require_permission("roles:read")),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """
    Get a role by ID.
    """
    auth_service = AuthService(db)
    role = auth_service.get_role(role_id)
    
    if not role:
        raise NotFoundError("Role not found")
    
    return RoleResponse.model_validate(role)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create role")
def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """
    Create a new role (admin only).
    """
    auth_service = AuthService(db)
    role = auth_service.create_role(role_data)
    
    return RoleResponse.model_validate(role)


@router.patch("/roles/{role_id}", response_model=RoleResponse, summary="Update role")
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """
    Update a role (admin only).
    """
    auth_service = AuthService(db)
    role = auth_service.update_role(role_id, role_data)
    
    return RoleResponse.model_validate(role)


@router.delete("/roles/{role_id}", response_model=MessageResponse, summary="Delete role")
def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a role (admin only).
    """
    auth_service = AuthService(db)
    auth_service.delete_role(role_id)
    
    return MessageResponse(message="Role deleted successfully")


@router.get("/roles/{role_id}/permissions", response_model=list[str], summary="Get role permissions")
def get_role_permissions(
    role_id: int,
    current_user: User = Depends(require_permission("roles:read")),
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Get permissions for a role.
    """
    auth_service = AuthService(db)
    permissions = auth_service.get_role_permissions(role_id)
    
    return permissions


@router.post("/roles/{role_id}/permissions", response_model=RoleResponse, summary="Assign permissions to role")
def assign_permissions(
    role_id: int,
    permission_names: list[str],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """
    Assign permissions to a role (admin only).
    """
    auth_service = AuthService(db)
    role = auth_service.assign_permissions(role_id, permission_names)
    
    return RoleResponse.model_validate(role)


@router.delete("/roles/{role_id}/permissions/{permission_name}", response_model=RoleResponse, summary="Remove permission from role")
def remove_permission(
    role_id: int,
    permission_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """
    Remove a permission from a role (admin only).
    """
    auth_service = AuthService(db)
    role = auth_service.remove_permission(role_id, permission_name)
    
    return RoleResponse.model_validate(role)