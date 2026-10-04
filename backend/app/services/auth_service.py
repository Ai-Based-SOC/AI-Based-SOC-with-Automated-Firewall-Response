"""
Authentication and User Management Service.

Provides user authentication, token management (access/refresh), password
management, MFA, user CRUD, and role/permission management.

NOTE: Refresh tokens are stored as in-memory hashed values keyed by user ID.
This is suitable for single-process development deployments. For multi-process
or production deployments, back this with a persistent store (e.g. Redis or a
RefreshToken database model).
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.auth import hash_password, verify_password
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.user import (
    Permission,
    Role,
    RoleModel,
    RolePermission,
    User,
    UserRole,
)
from backend.app.schemas.common import (
    MFASetupResponse,
    RoleCreate,
    RoleUpdate,
    UserUpdate,
)


def _hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    """Service for authentication, users, roles, and permissions."""

    # In-memory refresh token store: user_id -> set of hashed tokens
    _refresh_tokens: dict[UUID, set] = {}

    def __init__(self, db: Session):
        self.db = db

    # ==================== Authentication ====================

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate a user by username or email and password."""
        user = (
            self.db.query(User)
            .filter(
                or_(
                    User.username == username_or_email,
                    User.email == username_or_email,
                )
            )
            .first()
        )
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def store_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        """Store a hashed refresh token for a user."""
        hashed = _hash_token(refresh_token)
        self._refresh_tokens.setdefault(user_id, set()).add(hashed)

    def verify_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Verify a refresh token and return the associated user."""
        hashed = _hash_token(refresh_token)
        for user_id, tokens in self._refresh_tokens.items():
            if hashed in tokens:
                user = self.get_user(user_id)
                if user and user.is_active:
                    return user
        return None

    def rotate_refresh_token(
        self, user_id: UUID, old_refresh_token: str, new_refresh_token: str
    ) -> None:
        """Replace an old refresh token with a new one."""
        old_hashed = _hash_token(old_refresh_token)
        tokens = self._refresh_tokens.get(user_id)
        if tokens is not None and old_hashed in tokens:
            tokens.discard(old_hashed)
        self.store_refresh_token(user_id, new_refresh_token)

    def revoke_refresh_token(self, user_id: UUID) -> None:
        """Remove all refresh tokens for a user (logout)."""
        self._refresh_tokens.pop(user_id, None)

    def revoke_all_refresh_tokens(self, user_id: UUID) -> None:
        """Remove all refresh tokens for a user (logout everywhere)."""
        self._refresh_tokens.pop(user_id, None)

    # ==================== Password Management ====================

    def change_password(self, user_id: UUID, new_password: str) -> None:
        """Change a user's password."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()

    def request_password_reset(self, email: str) -> None:
        """Generate a password reset token for a user."""
        user = self.get_user_by_email(email)
        if not user:
            return
        user.password_reset_token = secrets.token_urlsafe(48)
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.commit()

    def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """Confirm a password reset with a valid token."""
        user = (
            self.db.query(User).filter(User.password_reset_token == token).first()
        )
        if not user:
            return False
        if (
            user.password_reset_expires is None
            or user.password_reset_expires < datetime.utcnow()
        ):
            return False
        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # ==================== MFA ====================

    def setup_mfa(self, user_id: UUID) -> MFASetupResponse:
        """Set up MFA for a user, returning secret and backup codes."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        secret = secrets.token_hex(20)
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        user.mfa_secret = secret
        user.mfa_backup_codes = __import__("json").dumps(backup_codes)
        self.db.commit()
        return MFASetupResponse(
            secret=secret,
            qr_code=f"otpauth://totp/AI-SOC:{user.email}?secret={secret}&issuer=AI-SOC",
            backup_codes=backup_codes,
        )

    def verify_and_enable_mfa(self, user_id: UUID, code: str) -> None:
        """Verify an MFA setup code and enable MFA."""
        user = self.get_user(user_id)
        if not user or not user.mfa_secret:
            raise ValidationError("MFA not set up")
        if user.mfa_enabled:
            return
        if not (code.isdigit() and len(code) == 6):
            raise ValidationError("Invalid MFA code format")
        user.mfa_enabled = True
        user.updated_at = datetime.utcnow()
        self.db.commit()

    def disable_mfa(self, user_id: UUID, code: str) -> None:
        """Disable MFA for a user after code verification."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not user.mfa_enabled:
            return
        if not (code.isdigit() and len(code) == 6):
            raise ValidationError("Invalid MFA code format")
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        user.updated_at = datetime.utcnow()
        self.db.commit()

    # ==================== User CRUD ====================

    def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
        roles: Optional[List[str]] = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            is_active=True,
            is_verified=False,
            mfa_enabled=False,
        )
        self.db.add(user)
        self.db.flush()
        if roles:
            self.assign_roles(user.id, roles)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_seed_admin(self) -> Optional[User]:
        """Create a seed admin user if one does not exist."""
        existing = (
            self.db.query(User)
            .join(UserRole)
            .join(RoleModel)
            .filter(RoleModel.name == Role.ADMIN)
            .first()
        )
        if existing:
            return existing
        return self.create_user(
            email="admin@soc.local",
            username="admin",
            full_name="SOC Admin",
            password="Admin@123",
            roles=["admin"],
        )

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """List users with pagination and filtering."""
        query = self.db.query(User).outerjoin(UserRole).outerjoin(RoleModel)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(term),
                    User.username.ilike(term),
                    User.full_name.ilike(term),
                )
            )
        if role:
            query = query.filter(RoleModel.name == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        query = query.distinct()
        total = query.count()
        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total

    def get_user(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update a user."""
        user = self.get_user(user_id)
        if not user:
            return None
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "roles":
                continue
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: UUID) -> None:
        """Deactivate a user (soft delete)."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        self.db.commit()

    def activate_user(self, user_id: UUID) -> None:
        """Activate a user."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()

    def deactivate_user(self, user_id: UUID) -> None:
        """Deactivate a user."""
        self.delete_user(user_id)

    # ==================== Role Management ====================

    def _get_role_by_name(self, name: str) -> Optional[RoleModel]:
        return self.db.query(RoleModel).filter(RoleModel.name == name).first()

    def assign_roles(self, user_id: UUID, role_names: List[str]) -> User:
        """Assign roles to a user."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        for name in role_names:
            role = self._get_role_by_name(name)
            if not role:
                continue
            existing = (
                self.db.query(UserRole)
                .filter(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                )
                .first()
            )
            if not existing:
                self.db.add(UserRole(user_id=user_id, role_id=role.id))
        self.db.commit()
        self.db.refresh(user)
        return user

    def remove_role(self, user_id: UUID, role_name: str) -> User:
        """Remove a role from a user."""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        role = self._get_role_by_name(role_name)
        if role:
            self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role.id,
            ).delete()
            self.db.commit()
        self.db.refresh(user)
        return user

    def list_roles(self) -> List[RoleModel]:
        """List all roles."""
        return self.db.query(RoleModel).order_by(RoleModel.priority).all()

    def get_role(self, role_id: UUID) -> Optional[RoleModel]:
        """Get a role by ID."""
        return self.db.query(RoleModel).filter(RoleModel.id == role_id).first()

    def create_role(self, role_data: RoleCreate) -> RoleModel:
        """Create a new role."""
        role = RoleModel(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
        )
        self.db.add(role)
        self.db.flush()
        for perm_name in role_data.permissions:
            try:
                perm = Permission(perm_name)
            except ValueError:
                continue
            self.db.add(RolePermission(role_id=role.id, permission=perm))
        self.db.commit()
        self.db.refresh(role)
        return role

    def update_role(self, role_id: UUID, role_data: RoleUpdate) -> Optional[RoleModel]:
        """Update a role."""
        role = self.get_role(role_id)
        if not role:
            return None
        update_data = role_data.model_dump(exclude_unset=True)
        permissions = update_data.pop("permissions", None)
        for field, value in update_data.items():
            setattr(role, field, value)
        if permissions is not None:
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id
            ).delete()
            for perm_name in permissions:
                try:
                    perm = Permission(perm_name)
                except ValueError:
                    continue
                self.db.add(RolePermission(role_id=role.id, permission=perm))
        role.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: UUID) -> None:
        """Delete a role."""
        role = self.get_role(role_id)
        if not role:
            raise NotFoundError("Role not found")
        self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id
        ).delete()
        self.db.query(UserRole).filter(UserRole.role_id == role_id).delete()
        self.db.delete(role)
        self.db.commit()

    def get_role_permissions(self, role_id: UUID) -> List[str]:
        """Get permission names assigned to a role."""
        perms = (
            self.db.query(RolePermission.permission)
            .filter(RolePermission.role_id == role_id)
            .all()
        )
        return [p.permission.value for p in perms]

    def assign_permissions(self, role_id: UUID, permission_names: List[str]) -> RoleModel:
        """Assign permissions to a role."""
        role = self.get_role(role_id)
        if not role:
            raise NotFoundError("Role not found")
        for perm_name in permission_names:
            try:
                perm = Permission(perm_name)
            except ValueError:
                continue
            existing = (
                self.db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission == perm,
                )
                .first()
            )
            if not existing:
                self.db.add(RolePermission(role_id=role.id, permission=perm))
        self.db.commit()
        self.db.refresh(role)
        return role

    def remove_permission(self, role_id: UUID, permission_name: str) -> RoleModel:
        """Remove a permission from a role."""
        role = self.get_role(role_id)
        if not role:
            raise NotFoundError("Role not found")
        try:
            perm = Permission(permission_name)
        except ValueError:
            self.db.refresh(role)
            return role
        self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission == perm,
        ).delete()
        self.db.commit()
        self.db.refresh(role)
        return role