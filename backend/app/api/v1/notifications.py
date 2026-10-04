"""
Notifications API routes.

Provides notification management, preferences, and delivery channels.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.notification import Notification, NotificationChannel, NotificationPriority
from backend.app.models.user import User
from backend.app.schemas.common import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationPreferences,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse], summary="List notifications")
def list_notifications(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    channel: Annotated[NotificationChannel | None, Query()] = None,
    priority: Annotated[NotificationPriority | None, Query()] = None,
    is_read: Annotated[bool | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[NotificationResponse]:
    """
    List notifications with pagination, search, and filtering.
    """
    notification_service = NotificationService(db)
    notifications, total = notification_service.list_notifications(
        page=page,
        page_size=page_size,
        search=search,
        channel=channel,
        priority=priority,
        is_read=is_read,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id,
    )
    
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", summary="Get notification statistics")
def get_notification_stats(
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get notification statistics for dashboard.
    """
    notification_service = NotificationService(db)
    return notification_service.get_stats(current_user.id)


@router.get("/{notification_id}", response_model=NotificationResponse, summary="Get notification by ID")
def get_notification(
    notification_id: int,
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """
    Get a notification by ID.
    """
    notification_service = NotificationService(db)
    notification = notification_service.get_notification(notification_id, current_user.id)
    
    if not notification:
        raise NotFoundError("Notification not found")
    
    return NotificationResponse.model_validate(notification)


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED, summary="Create notification")
def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(require_permission("notifications:write")),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """
    Create a new notification.
    """
    notification_service = NotificationService(db)
    notification = notification_service.create_notification(notification_data, current_user.id)
    
    return NotificationResponse.model_validate(notification)


@router.post("/broadcast", response_model=MessageResponse, summary="Broadcast notification")
def broadcast_notification(
    notification_data: NotificationCreate,
    user_ids: list[int] | None = None,
    role_names: list[str] | None = None,
    current_user: User = Depends(require_permission("notifications:write")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Broadcast a notification to multiple users or roles.
    """
    notification_service = NotificationService(db)
    count = notification_service.broadcast_notification(
        notification_data, 
        user_ids, 
        role_names, 
        current_user.id
    )
    
    return MessageResponse(message=f"Notification sent to {count} users")


@router.patch("/{notification_id}", response_model=NotificationResponse, summary="Update notification")
def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    current_user: User = Depends(require_permission("notifications:write")),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """
    Update a notification.
    """
    notification_service = NotificationService(db)
    notification = notification_service.update_notification(notification_id, notification_data, current_user.id)
    
    if not notification:
        raise NotFoundError("Notification not found")
    
    return NotificationResponse.model_validate(notification)


@router.post("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """
    Mark a notification as read.
    """
    notification_service = NotificationService(db)
    notification = notification_service.mark_read(notification_id, current_user.id)
    
    if not notification:
        raise NotFoundError("Notification not found")
    
    return NotificationResponse.model_validate(notification)


@router.post("/read-all", response_model=MessageResponse, summary="Mark all notifications as read")
def mark_all_read(
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Mark all notifications as read for current user.
    """
    notification_service = NotificationService(db)
    count = notification_service.mark_all_read(current_user.id)
    
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.delete("/{notification_id}", response_model=MessageResponse, summary="Delete notification")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(require_permission("notifications:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a notification.
    """
    notification_service = NotificationService(db)
    notification_service.delete_notification(notification_id, current_user.id)
    
    return MessageResponse(message="Notification deleted successfully")


# =========================================================
# Notification Preferences
# =========================================================

@router.get("/preferences", response_model=NotificationPreferences, summary="Get notification preferences")
def get_preferences(
    current_user: User = Depends(require_permission("notifications:read")),
    db: Session = Depends(get_db),
) -> NotificationPreferences:
    """
    Get notification preferences for current user.
    """
    notification_service = NotificationService(db)
    return notification_service.get_preferences(current_user.id)


@router.patch("/preferences", response_model=NotificationPreferences, summary="Update notification preferences")
def update_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(require_permission("notifications:write")),
    db: Session = Depends(get_db),
) -> NotificationPreferences:
    """
    Update notification preferences for current user.
    """
    notification_service = NotificationService(db)
    return notification_service.update_preferences(current_user.id, preferences)


# =========================================================
# Notification Channels
# =========================================================

@router.get("/channels", summary="List notification channels")
def list_channels(
    current_user: User = Depends(require_permission("notifications:read")),
) -> list[dict]:
    """
    List available notification channels.
    """
    return [
        {
            "name": "email",
            "display_name": "Email",
            "supports_priority": True,
            "supports_rich_content": True,
        },
        {
            "name": "sms",
            "display_name": "SMS",
            "supports_priority": True,
            "supports_rich_content": False,
        },
        {
            "name": "slack",
            "display_name": "Slack",
            "supports_priority": True,
            "supports_rich_content": True,
        },
        {
            "name": "teams",
            "display_name": "Microsoft Teams",
            "supports_priority": True,
            "supports_rich_content": True,
        },
        {
            "name": "webhook",
            "display_name": "Webhook",
            "supports_priority": True,
            "supports_rich_content": True,
        },
        {
            "name": "pushover",
            "display_name": "Pushover",
            "supports_priority": True,
            "supports_rich_content": False,
        },
        {
            "name": "in_app",
            "display_name": "In-App",
            "supports_priority": True,
            "supports_rich_content": True,
        },
    ]


@router.post("/channels/{channel}/test", summary="Test notification channel")
def test_channel(
    channel: str,
    config: dict,
    current_user: User = Depends(require_permission("notifications:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Test a notification channel configuration.
    """
    notification_service = NotificationService(db)
    return notification_service.test_channel(channel, config)