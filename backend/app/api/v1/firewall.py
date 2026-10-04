"""
Firewall API routes.

Provides firewall rule management, execution, and automation across multiple platforms.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.core.rbac import require_permission
from backend.app.db.session import get_db
from backend.app.models.firewall import FirewallRule, FirewallAction, FirewallProvider, FirewallRuleStatus
from backend.app.models.user import User
from backend.app.schemas.common import (
    FirewallRuleCreate,
    FirewallRuleResponse,
    FirewallRuleUpdate,
    FirewallExecutionRequest,
    FirewallExecutionResponse,
    MessageResponse,
    PaginatedResponse,
)
from backend.app.services.firewall_service import FirewallService

router = APIRouter(prefix="/firewall", tags=["Firewall"])


@router.get("/rules", response_model=PaginatedResponse[FirewallRuleResponse], summary="List firewall rules")
def list_firewall_rules(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    platform: Annotated[str | None, Query()] = None,
    action: Annotated[FirewallAction | None, Query()] = None,
    status: Annotated[FirewallRuleStatus | None, Query()] = None,
    enabled: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    current_user: User = Depends(require_permission("firewall:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[FirewallRuleResponse]:
    """
    List firewall rules with pagination, search, and filtering.
    """
    firewall_service = FirewallService(db)
    rules, total = firewall_service.list_rules(
        page=page,
        page_size=page_size,
        search=search,
        platform=platform,
        action=action,
        status=status,
        enabled=enabled,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedResponse(
        items=[FirewallRuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/rules/stats", summary="Get firewall rule statistics")
def get_firewall_stats(
    current_user: User = Depends(require_permission("firewall:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get firewall rule statistics for dashboard.
    """
    firewall_service = FirewallService(db)
    return firewall_service.get_stats()


@router.get("/rules/{rule_id}", response_model=FirewallRuleResponse, summary="Get firewall rule by ID")
def get_firewall_rule(
    rule_id: int,
    current_user: User = Depends(require_permission("firewall:read")),
    db: Session = Depends(get_db),
) -> FirewallRuleResponse:
    """
    Get a firewall rule by ID.
    """
    firewall_service = FirewallService(db)
    rule = firewall_service.get_rule(rule_id)
    
    if not rule:
        raise NotFoundError("Firewall rule not found")
    
    return FirewallRuleResponse.model_validate(rule)


@router.post("/rules", response_model=FirewallRuleResponse, status_code=status.HTTP_201_CREATED, summary="Create firewall rule")
def create_firewall_rule(
    rule_data: FirewallRuleCreate,
    current_user: User = Depends(require_permission("firewall:write")),
    db: Session = Depends(get_db),
) -> FirewallRuleResponse:
    """
    Create a new firewall rule.
    """
    firewall_service = FirewallService(db)
    rule = firewall_service.create_rule(rule_data, current_user.id)
    
    return FirewallRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=FirewallRuleResponse, summary="Update firewall rule")
def update_firewall_rule(
    rule_id: int,
    rule_data: FirewallRuleUpdate,
    current_user: User = Depends(require_permission("firewall:write")),
    db: Session = Depends(get_db),
) -> FirewallRuleResponse:
    """
    Update a firewall rule.
    """
    firewall_service = FirewallService(db)
    rule = firewall_service.update_rule(rule_id, rule_data, current_user.id)
    
    if not rule:
        raise NotFoundError("Firewall rule not found")
    
    return FirewallRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/enable", response_model=FirewallRuleResponse, summary="Enable firewall rule")
def enable_firewall_rule(
    rule_id: int,
    current_user: User = Depends(require_permission("firewall:write")),
    db: Session = Depends(get_db),
) -> FirewallRuleResponse:
    """
    Enable a firewall rule.
    """
    firewall_service = FirewallService(db)
    rule = firewall_service.enable_rule(rule_id, current_user.id)
    
    if not rule:
        raise NotFoundError("Firewall rule not found")
    
    return FirewallRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/disable", response_model=FirewallRuleResponse, summary="Disable firewall rule")
def disable_firewall_rule(
    rule_id: int,
    current_user: User = Depends(require_permission("firewall:write")),
    db: Session = Depends(get_db),
) -> FirewallRuleResponse:
    """
    Disable a firewall rule.
    """
    firewall_service = FirewallService(db)
    rule = firewall_service.disable_rule(rule_id, current_user.id)
    
    if not rule:
        raise NotFoundError("Firewall rule not found")
    
    return FirewallRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/deploy", response_model=FirewallExecutionResponse, summary="Deploy firewall rule")
def deploy_firewall_rule(
    rule_id: int,
    execution_request: FirewallExecutionRequest,
    current_user: User = Depends(require_permission("firewall:execute")),
    db: Session = Depends(get_db),
) -> FirewallExecutionResponse:
    """
    Deploy a firewall rule to the target platform.
    """
    firewall_service = FirewallService(db)
    result = firewall_service.deploy_rule(rule_id, execution_request, current_user.id)
    
    return FirewallExecutionResponse(**result)


@router.post("/rules/{rule_id}/rollback", response_model=FirewallExecutionResponse, summary="Rollback firewall rule")
def rollback_firewall_rule(
    rule_id: int,
    execution_request: FirewallExecutionRequest,
    current_user: User = Depends(require_permission("firewall:execute")),
    db: Session = Depends(get_db),
) -> FirewallExecutionResponse:
    """
    Rollback a deployed firewall rule.
    """
    firewall_service = FirewallService(db)
    result = firewall_service.rollback_rule(rule_id, execution_request, current_user.id)
    
    return FirewallExecutionResponse(**result)


@router.post("/rules/{rule_id}/validate", summary="Validate firewall rule")
def validate_firewall_rule(
    rule_id: int,
    current_user: User = Depends(require_permission("firewall:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Validate a firewall rule syntax and logic.
    """
    firewall_service = FirewallService(db)
    return firewall_service.validate_rule(rule_id)


@router.post("/rules/bulk-deploy", response_model=FirewallExecutionResponse, summary="Bulk deploy firewall rules")
def bulk_deploy_firewall_rules(
    execution_request: FirewallExecutionRequest,
    rule_ids: list[int],
    current_user: User = Depends(require_permission("firewall:execute")),
    db: Session = Depends(get_db),
) -> FirewallExecutionResponse:
    """
    Deploy multiple firewall rules in bulk.
    """
    firewall_service = FirewallService(db)
    result = firewall_service.bulk_deploy(rule_ids, execution_request, current_user.id)
    
    return FirewallExecutionResponse(**result)


@router.delete("/rules/{rule_id}", response_model=MessageResponse, summary="Delete firewall rule")
def delete_firewall_rule(
    rule_id: int,
    current_user: User = Depends(require_permission("firewall:delete")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Delete a firewall rule (admin only).
    """
    firewall_service = FirewallService(db)
    firewall_service.delete_rule(rule_id)
    
    return MessageResponse(message="Firewall rule deleted successfully")


# =========================================================
# Firewall Platforms
# =========================================================

@router.get("/platforms", summary="List supported firewall platforms")
def list_platforms(
    current_user: User = Depends(require_permission("firewall:read")),
) -> list[dict]:
    """
    List supported firewall platforms and their capabilities.
    """
    return [
        {
            "name": "windows",
            "display_name": "Windows Firewall",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
        {
            "name": "ufw",
            "display_name": "UFW (Uncomplicated Firewall)",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
        {
            "name": "iptables",
            "display_name": "iptables",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
        {
            "name": "pfsense",
            "display_name": "pfSense",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
        {
            "name": "aws_sg",
            "display_name": "AWS Security Groups",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": False,
        },
        {
            "name": "azure_nsg",
            "display_name": "Azure Network Security Groups",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
        {
            "name": "gcp_firewall",
            "display_name": "GCP Firewall Rules",
            "supports_ingress": True,
            "supports_egress": True,
            "supports_logging": True,
        },
    ]


@router.get("/platforms/{platform}/status", summary="Get platform connection status")
def get_platform_status(
    platform: str,
    current_user: User = Depends(require_permission("firewall:read")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get connection status for a firewall platform.
    """
    firewall_service = FirewallService(db)
    return firewall_service.get_platform_status(platform)


@router.post("/platforms/{platform}/test", summary="Test platform connection")
def test_platform_connection(
    platform: str,
    config: dict,
    current_user: User = Depends(require_permission("firewall:write")),
    db: Session = Depends(get_db),
) -> dict:
    """
    Test connection to a firewall platform.
    """
    firewall_service = FirewallService(db)
    return firewall_service.test_platform_connection(platform, config)