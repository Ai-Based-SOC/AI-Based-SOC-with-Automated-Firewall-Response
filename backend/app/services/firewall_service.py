"""
Firewall Service for the AI-SOC Platform.

Provides enterprise-grade firewall automation with multi-platform support,
approval workflows, rollback capabilities, and comprehensive audit logging.
"""
import asyncio
import ipaddress
import json
import platform
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.db.session import get_db_session
from backend.app.models.firewall import (
    FirewallAction,
    FirewallAuditLog,
    FirewallProvider,
    FirewallProviderConfig,
    FirewallRule,
    FirewallRuleStatus,
)
from backend.app.models.user import User
from backend.app.schemas.common import (
    FirewallActionRequest,
    FirewallActionResponse,
    FirewallRuleCreate,
    FirewallRuleResponse,
    FirewallRuleUpdate,
    FirewallExecutionRequest,
    FirewallExecutionResponse,
    PaginatedResponse,
)


class FirewallService:
    """
    Enterprise-grade Firewall Automation Service.
    
    Features:
    - Multi-platform firewall support (Windows, Linux iptables, UFW, pfSense, Cloud)
    - Approval workflows with configurable policies
    - Rollback and transaction support
    - Simulation mode for safe testing
    - Comprehensive audit logging
    - Bulk operations with concurrency control
    - Integration with threat intelligence
    - Rule lifecycle management
    - Metrics and monitoring
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._adapters = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        """Initialize firewall adapters from database configuration."""
        configs = self.db.query(FirewallProviderConfig).filter(
            FirewallProviderConfig.is_active == True
        ).all()
        
        for config in configs:
            self._adapters[config.provider] = self._create_adapter(config)

    def _create_adapter(self, config: FirewallProviderConfig) -> dict:
        """Create adapter configuration from provider config."""
        return {
            "provider": config.provider.value,
            "config": config.config,
            "simulation_mode": config.simulation_mode,
            "requires_approval": config.requires_approval,
            "default_expire_hours": config.default_expire_hours,
            "max_rules": config.max_rules,
        }

    def _get_adapter(self, provider: FirewallProvider) -> Optional[dict]:
        """Get adapter for a provider."""
        return self._adapters.get(provider)

    # =========================================================
    # Rule Management
    # =========================================================

    def list_rules(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        platform: Optional[str] = None,
        action: Optional[FirewallAction] = None,
        status: Optional[FirewallRuleStatus] = None,
        enabled: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[FirewallRule], int]:
        """List firewall rules with pagination, search, and filtering."""
        query = self.db.query(FirewallRule)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    FirewallRule.name.ilike(search_term),
                    FirewallRule.description.ilike(search_term),
                    FirewallRule.rule_id.ilike(search_term),
                    FirewallRule.source_ip.ilike(search_term),
                )
            )

        if platform:
            try:
                provider = FirewallProvider(platform)
                query = query.filter(FirewallRule.provider == provider)
            except ValueError:
                pass

        if action:
            query = query.filter(FirewallRule.action == action)

        if status:
            query = query.filter(FirewallRule.status == status)

        if enabled is not None:
            query = query.filter(FirewallRule.enabled == enabled)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr(FirewallRule, sort_by, FirewallRule.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Apply pagination
        offset = (page - 1) * page_size
        rules = query.offset(offset).limit(page_size).all()

        return rules, total

    def get_stats(self) -> dict:
        """Get firewall rule statistics for dashboard."""
        total = self.db.query(FirewallRule).count()
        active = self.db.query(FirewallRule).filter(
            FirewallRule.status == FirewallRuleStatus.ACTIVE
        ).count()
        pending = self.db.query(FirewallRule).filter(
            FirewallRule.status == FirewallRuleStatus.PENDING
        ).count()
        failed = self.db.query(FirewallRule).filter(
            FirewallRule.status == FirewallRuleStatus.FAILED
        ).count()
        expired = self.db.query(FirewallRule).filter(
            FirewallRule.status == FirewallRuleStatus.EXPIRED
        ).count()
        simulated = self.db.query(FirewallRule).filter(
            FirewallRule.status == FirewallRuleStatus.SIMULATED
        ).count()

        # By provider
        by_provider = {}
        for provider in FirewallProvider:
            count = self.db.query(FirewallRule).filter(
                FirewallRule.provider == provider
            ).count()
            if count > 0:
                by_provider[provider.value] = count

        # By action
        by_action = {}
        for action in FirewallAction:
            count = self.db.query(FirewallRule).filter(
                FirewallRule.action == action
            ).count()
            if count > 0:
                by_action[action.value] = count

        # Recent activity (last 24h)
        from datetime import timedelta
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = self.db.query(FirewallRule).filter(
            FirewallRule.created_at >= day_ago
        ).count()

        return {
            "total_rules": total,
            "active_rules": active,
            "pending_rules": pending,
            "failed_rules": failed,
            "expired_rules": expired,
            "simulated_rules": simulated,
            "recent_24h": recent,
            "by_provider": by_provider,
            "by_action": by_action,
        }

    def get_rule(self, rule_id: int) -> Optional[FirewallRule]:
        """Get a firewall rule by ID."""
        return self.db.query(FirewallRule).filter(FirewallRule.id == rule_id).first()

    def get_rule_by_rule_id(self, rule_id: str) -> Optional[FirewallRule]:
        """Get a firewall rule by rule_id string."""
        return self.db.query(FirewallRule).filter(FirewallRule.rule_id == rule_id).first()

    def create_rule(self, rule_data: FirewallRuleCreate, created_by: UUID) -> FirewallRule:
        """Create a new firewall rule."""
        # Validate IP addresses
        if rule_data.source_ip:
            try:
                ipaddress.ip_network(rule_data.source_ip, strict=False)
            except ValueError:
                raise ValidationError("Invalid source IP address or CIDR")

        if rule_data.destination_ip:
            try:
                ipaddress.ip_network(rule_data.destination_ip, strict=False)
            except ValueError:
                raise ValidationError("Invalid destination IP address or CIDR")

        # Validate provider
        try:
            provider = FirewallProvider(rule_data.adapter)
        except ValueError:
            raise ValidationError(f"Unsupported firewall adapter: {rule_data.adapter}")

        # Check if adapter is configured
        adapter = self._get_adapter(provider)
        if not adapter:
            raise ValidationError(f"Firewall adapter not configured: {provider.value}")

        # Generate unique rule_id
        rule_id = f"fw_{provider.value}_{int(time.time())}_{uuid4().hex[:8]}"

        # Create rule
        rule = FirewallRule(
            rule_id=rule_id,
            name=rule_data.name,
            description=rule_data.description,
            action=FirewallAction(rule_data.action),
            provider=provider,
            source_ip=rule_data.source_ip,
            destination_ip=rule_data.destination_ip,
            source_port=rule_data.source_port,
            destination_port=rule_data.destination_port,
            protocol=rule_data.protocol,
            direction=rule_data.direction,
            priority=rule_data.priority,
            enabled=rule_data.enabled,
            status=FirewallRuleStatus.PENDING,
            requires_approval=adapter.get("requires_approval", True),
            is_simulation=adapter.get("simulation_mode", True),
            created_by_id=created_by,
            tags=[],
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        self._create_audit_log(
            rule_id=rule.id,
            user_id=created_by,
            action="created",
            new_status=FirewallRuleStatus.PENDING,
            details={"rule_data": rule_data.model_dump()},
        )

        return rule

    def update_rule(
        self, rule_id: int, rule_data: FirewallRuleUpdate, updated_by: UUID
    ) -> Optional[FirewallRule]:
        """Update a firewall rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        # Store previous status for audit
        previous_status = rule.status

        # Update fields
        update_data = rule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "action" and value:
                value = FirewallAction(value)
            if field == "protocol" and value:
                value = value.lower()
            setattr(rule, field, value)

        rule.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        self._create_audit_log(
            rule_id=rule.id,
            user_id=updated_by,
            action="updated",
            previous_status=previous_status,
            new_status=rule.status,
            details={"updated_fields": update_data},
        )

        return rule

    def enable_rule(self, rule_id: int, enabled_by: UUID) -> Optional[FirewallRule]:
        """Enable a firewall rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        previous_status = rule.status
        rule.enabled = True
        rule.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)

        self._create_audit_log(
            rule_id=rule.id,
            user_id=enabled_by,
            action="enabled",
            previous_status=previous_status,
            new_status=rule.status,
        )

        return rule

    def disable_rule(self, rule_id: int, disabled_by: UUID) -> Optional[FirewallRule]:
        """Disable a firewall rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        previous_status = rule.status
        rule.enabled = False
        rule.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)

        self._create_audit_log(
            rule_id=rule.id,
            user_id=disabled_by,
            action="disabled",
            previous_status=previous_status,
            new_status=rule.status,
        )

        return rule

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a firewall rule (admin only)."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise NotFoundError("Firewall rule not found")

        # If rule is active, rollback first
        if rule.status == FirewallRuleStatus.ACTIVE:
            self.rollback_rule(rule_id, FirewallExecutionRequest(simulation_mode=False), UUID(int=0))

        self.db.delete(rule)
        self.db.commit()
        return True

    # =========================================================
    # Rule Execution (Deploy/Rollback)
    # =========================================================

    def deploy_rule(
        self, rule_id: int, execution_request: FirewallExecutionRequest, executed_by: UUID
    ) -> dict:
        """Deploy a firewall rule to the target platform."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise NotFoundError("Firewall rule not found")

        if not rule.enabled:
            raise ValidationError("Cannot deploy disabled rule")

        if rule.status == FirewallRuleStatus.ACTIVE:
            raise ValidationError("Rule is already active")

        # Check approval
        if rule.requires_approval and rule.status != FirewallRuleStatus.PENDING:
            if rule.approved_by_id is None:
                raise ValidationError("Rule requires approval before deployment")

        # Get adapter
        adapter = self._get_adapter(rule.provider)
        if not adapter:
            raise ValidationError(f"No adapter configured for provider: {rule.provider.value}")

        # Determine simulation mode
        simulation_mode = execution_request.simulation_mode or rule.is_simulation

        # Generate commands for the platform
        commands = self._generate_commands(rule, "apply")
        
        # Execute commands
        start_time = time.time()
        result = self._execute_commands(adapter, commands, simulation_mode)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Update rule status
        previous_status = rule.status
        if result["success"]:
            rule.status = FirewallRuleStatus.SIMULATED if simulation_mode else FirewallRuleStatus.ACTIVE
            rule.applied_at = datetime.now(timezone.utc)
            rule.applied_by_id = executed_by
            rule.provider_rule_id = result.get("provider_rule_id")
            rule.simulation_result = result if simulation_mode else None
        else:
            rule.status = FirewallRuleStatus.FAILED

        rule.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        self._create_audit_log(
            rule_id=rule.id,
            user_id=executed_by,
            action="deployed" if not simulation_mode else "simulated",
            previous_status=previous_status,
            new_status=rule.status,
            details={
                "commands": commands,
                "result": result,
                "simulation_mode": simulation_mode,
            },
            execution_time_ms=execution_time_ms,
            provider_response=result,
        )

        return {
            "success": result["success"],
            "message": result.get("message", "Rule deployed successfully" if not simulation_mode else "Rule simulated successfully"),
            "rule_id": str(rule.id),
            "provider_rule_id": rule.provider_rule_id,
            "status": rule.status.value,
            "simulation_mode": simulation_mode,
            "execution_time_ms": execution_time_ms,
            "details": result,
        }

    def rollback_rule(
        self, rule_id: int, execution_request: FirewallExecutionRequest, executed_by: UUID
    ) -> dict:
        """Rollback a deployed firewall rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise NotFoundError("Firewall rule not found")

        if rule.status not in [FirewallRuleStatus.ACTIVE, FirewallRuleStatus.SIMULATED]:
            raise ValidationError(f"Cannot rollback rule in status: {rule.status.value}")

        # Get adapter
        adapter = self._get_adapter(rule.provider)
        if not adapter:
            raise ValidationError(f"No adapter configured for provider: {rule.provider.value}")

        # Determine simulation mode
        simulation_mode = execution_request.simulation_mode or rule.is_simulation

        # Generate rollback commands
        commands = self._generate_commands(rule, "rollback")
        
        # Execute rollback
        start_time = time.time()
        result = self._execute_commands(adapter, commands, simulation_mode)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Update rule status
        previous_status = rule.status
        if result["success"]:
            rule.status = FirewallRuleStatus.ROLLED_BACK
            rule.rolled_back_at = datetime.now(timezone.utc)
            rule.rollback_reason = execution_request.reason or "Manual rollback"
        else:
            rule.status = FirewallRuleStatus.FAILED

        rule.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        self._create_audit_log(
            rule_id=rule.id,
            user_id=executed_by,
            action="rolled_back",
            previous_status=previous_status,
            new_status=rule.status,
            details={
                "commands": commands,
                "result": result,
                "simulation_mode": simulation_mode,
                "reason": execution_request.reason,
            },
            execution_time_ms=execution_time_ms,
            provider_response=result,
        )

        return {
            "success": result["success"],
            "message": result.get("message", "Rule rolled back successfully"),
            "rule_id": str(rule.id),
            "status": rule.status.value,
            "simulation_mode": simulation_mode,
            "execution_time_ms": execution_time_ms,
            "details": result,
        }

    def validate_rule(self, rule_id: int) -> dict:
        """Validate a firewall rule syntax and logic."""
        rule = self.get_rule(rule_id)
        if not rule:
            raise NotFoundError("Firewall rule not found")

        errors = []
        warnings = []

        # Validate IP addresses
        if rule.source_ip:
            try:
                ipaddress.ip_network(rule.source_ip, strict=False)
            except ValueError:
                errors.append(f"Invalid source IP/CIDR: {rule.source_ip}")

        if rule.destination_ip:
            try:
                ipaddress.ip_network(rule.destination_ip, strict=False)
            except ValueError:
                errors.append(f"Invalid destination IP/CIDR: {rule.destination_ip}")

        # Validate ports
        if rule.source_port and (rule.source_port < 1 or rule.source_port > 65535):
            errors.append(f"Invalid source port: {rule.source_port}")

        if rule.destination_port and (rule.destination_port < 1 or rule.destination_port > 65535):
            errors.append(f"Invalid destination port: {rule.destination_port}")

        # Validate protocol
        valid_protocols = ["tcp", "udp", "icmp", "any", None]
        if rule.protocol and rule.protocol.lower() not in valid_protocols:
            warnings.append(f"Unusual protocol: {rule.protocol}")

        # Validate direction
        valid_directions = ["inbound", "outbound", "both"]
        if rule.direction not in valid_directions:
            errors.append(f"Invalid direction: {rule.direction}")

        # Check adapter availability
        adapter = self._get_adapter(rule.provider)
        if not adapter:
            errors.append(f"No adapter configured for provider: {rule.provider.value}")

        # Check for overlapping rules
        overlapping = self._check_overlapping_rules(rule)
        if overlapping:
            warnings.append(f"Potential overlap with {len(overlapping)} existing rule(s)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "rule_id": str(rule.id),
        }

    def bulk_deploy(
        self, rule_ids: list[int], execution_request: FirewallExecutionRequest, executed_by: UUID
    ) -> dict:
        """Deploy multiple firewall rules in bulk."""
        import time
        start_time = time.time()
        results = []
        successful = 0
        failed = 0
        first_rule_id = None

        for rule_id in rule_ids:
            try:
                result = self.deploy_rule(rule_id, execution_request, executed_by)
                if first_rule_id is None:
                    first_rule_id = str(rule_id)
                results.append({"rule_id": rule_id, **result})
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                results.append({
                    "rule_id": rule_id,
                    "success": False,
                    "message": str(e),
                    "error": str(e),
                })
                failed += 1

        return {
            "success": failed == 0,
            "message": f"Bulk deploy completed: {successful} successful, {failed} failed",
            "rule_id": first_rule_id,
            "execution_time": time.time() - start_time,
            "details": {
                "total": len(rule_ids),
                "successful": successful,
                "failed": failed,
                "results": results,
            },
        }

    # =========================================================
    # Quick Actions (Block/Unblock IP)
    # =========================================================

    def block_ip(self, request: FirewallActionRequest, requested_by: UUID) -> FirewallActionResponse:
        """Quick block an IP address."""
        # Validate IP
        try:
            ipaddress.ip_address(request.ip_address)
        except ValueError:
            raise ValidationError("Invalid IP address")

        # Find default provider or use specified
        adapter_name = request.adapter
        if not adapter_name:
            # Find first active provider that supports blocking
            config = self.db.query(FirewallProviderConfig).filter(
                FirewallProviderConfig.is_active == True,
                FirewallProviderConfig.provider.in_([
                    FirewallProvider.WINDOWS_FIREWALL,
                    FirewallProvider.UFW,
                    FirewallProvider.IPTABLES,
                    FirewallProvider.PFSENSE,
                ])
            ).first()
            if not config:
                raise ValidationError("No suitable firewall adapter configured")
            adapter_name = config.provider.value

        try:
            provider = FirewallProvider(adapter_name)
        except ValueError:
            raise ValidationError(f"Unsupported firewall adapter: {adapter_name}")

        adapter = self._get_adapter(provider)
        if not adapter:
            raise ValidationError(f"Firewall adapter not configured: {provider.value}")

        # Create rule
        rule_id = f"fw_block_{request.ip_address.replace('.', '_').replace(':', '_')}_{int(time.time())}"
        
        rule = FirewallRule(
            rule_id=rule_id,
            name=f"Block {request.ip_address}",
            description=request.reason,
            action=FirewallAction.BLOCK,
            provider=provider,
            source_ip=request.ip_address,
            direction="inbound",
            priority=100,
            enabled=True,
            status=FirewallRuleStatus.PENDING,
            requires_approval=adapter.get("requires_approval", True),
            is_simulation=adapter.get("simulation_mode", True),
            created_by_id=requested_by,
            expires_at=None,
            tags=["quick_block", "auto_generated"],
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # Auto-approve if not required
        if not rule.requires_approval:
            rule.approved_by_id = requested_by
            rule.approved_at = datetime.now(timezone.utc)
            self.db.commit()

        # Deploy if approved or no approval needed
        if rule.approved_by_id or not rule.requires_approval:
            exec_request = FirewallExecutionRequest(simulation_mode=rule.is_simulation)
            deploy_result = self.deploy_rule(rule.id, exec_request, requested_by)
            
            return FirewallActionResponse(
                success=deploy_result["success"],
                message=deploy_result["message"],
                ip_address=request.ip_address,
                action="block",
                rule_id=str(rule.id),
                expires_at=rule.expires_at,
            )

        return FirewallActionResponse(
            success=True,
            message="Block rule created, pending approval",
            ip_address=request.ip_address,
            action="block",
            rule_id=str(rule.id),
            expires_at=rule.expires_at,
        )

    def block_ip_from_threat_intel(
        self,
        ip_address: str,
        confidence: int,
        severity: str,
        source: str,
        context: dict,
        requested_by: UUID,
    ) -> FirewallActionResponse:
        """
        Block an IP address based on threat intelligence enrichment results.

        This method respects:
        - Existing approval workflow
        - Simulation/dry-run mode
        - Duplicate rule prevention
        - Audit logging

        Args:
            ip_address: The IP address to block
            confidence: Threat intelligence confidence score (0-100)
            severity: Threat severity (low, medium, high, critical)
            source: Source of the threat intelligence (e.g., "virustotal", "abuseipdb")
            context: Additional context from threat intel (tags, references, etc.)
            requested_by: User ID requesting the block

        Returns:
            FirewallActionResponse with block operation result
        """
        # Validate IP address
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            raise ValidationError("Invalid IP address")

        # Check for existing active block rule for this IP to prevent duplicates
        existing_rule = self.db.query(FirewallRule).filter(
            FirewallRule.source_ip == ip_address,
            FirewallRule.action == FirewallAction.BLOCK,
            FirewallRule.status == FirewallRuleStatus.ACTIVE,
            FirewallRule.enabled == True,
        ).first()

        if existing_rule:
            logger.info(f"Active block rule already exists for IP {ip_address}: {existing_rule.rule_id}")
            return FirewallActionResponse(
                success=True,
                message=f"IP {ip_address} already blocked by existing rule",
                ip_address=ip_address,
                action="block",
                rule_id=str(existing_rule.id),
                expires_at=existing_rule.expires_at,
            )

        # Find default Windows Firewall provider
        config = self.db.query(FirewallProviderConfig).filter(
            FirewallProviderConfig.is_active == True,
            FirewallProviderConfig.provider == FirewallProvider.WINDOWS_FIREWALL,
        ).first()

        if not config:
            raise ValidationError("Windows Firewall adapter not configured")

        adapter = self._get_adapter(FirewallProvider.WINDOWS_FIREWALL)
        if not adapter:
            raise ValidationError("Windows Firewall adapter not configured")

        # Build description with threat intel context
        tags = context.get("tags", [])
        references = context.get("references", [])
        description = (
            f"Threat Intel Auto-Block: {source} | "
            f"Confidence: {confidence}% | Severity: {severity}"
        )
        if tags:
            description += f" | Tags: {', '.join(tags[:5])}"
        if references:
            description += f" | Refs: {', '.join(references[:2])}"

        # Create rule
        rule_id = f"fw_ti_block_{ip_address.replace('.', '_').replace(':', '_')}_{int(time.time())}"

        rule = FirewallRule(
            rule_id=rule_id,
            name=f"ThreatIntel Block {ip_address}",
            description=description,
            action=FirewallAction.BLOCK,
            provider=FirewallProvider.WINDOWS_FIREWALL,
            source_ip=ip_address,
            direction="inbound",
            priority=100,
            enabled=True,
            status=FirewallRuleStatus.PENDING,
            requires_approval=adapter.get("requires_approval", True),
            is_simulation=adapter.get("simulation_mode", True),
            created_by_id=requested_by,
            expires_at=None,
            tags=["threat_intel", "auto_generated", source],
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # Auto-approve if not required
        if not rule.requires_approval:
            rule.approved_by_id = requested_by
            rule.approved_at = datetime.now(timezone.utc)
            self.db.commit()

        # Deploy if approved or no approval needed
        if rule.approved_by_id or not rule.requires_approval:
            exec_request = FirewallExecutionRequest(simulation_mode=rule.is_simulation)
            deploy_result = self.deploy_rule(rule.id, exec_request, requested_by)

            return FirewallActionResponse(
                success=deploy_result["success"],
                message=deploy_result["message"],
                ip_address=ip_address,
                action="block",
                rule_id=str(rule.id),
                expires_at=rule.expires_at,
            )

        return FirewallActionResponse(
            success=True,
            message="Threat intel block rule created, pending approval",
            ip_address=ip_address,
            action="block",
            rule_id=str(rule.id),
            expires_at=rule.expires_at,
        )

    def unblock_ip(self, request: FirewallActionRequest, requested_by: UUID) -> FirewallActionResponse:
        """Quick unblock an IP address."""
        # Find active block rule for this IP
        rule = self.db.query(FirewallRule).filter(
            FirewallRule.source_ip == request.ip_address,
            FirewallRule.action == FirewallAction.BLOCK,
            FirewallRule.status == FirewallRuleStatus.ACTIVE,
            FirewallRule.enabled == True,
        ).first()

        if not rule:
            raise NotFoundError("No active block rule found for this IP")

        # Rollback the rule
        exec_request = FirewallExecutionRequest(
            simulation_mode=rule.is_simulation,
            reason=request.reason,
        )
        rollback_result = self.rollback_rule(rule.id, exec_request, requested_by)

        return FirewallActionResponse(
            success=rollback_result["success"],
            message=rollback_result["message"],
            ip_address=request.ip_address,
            action="unblock",
            rule_id=str(rule.id),
        )

    # =========================================================
    # Platform Management
    # =========================================================

    def get_platform_status(self, platform: str) -> dict:
        """Get connection status for a firewall platform."""
        try:
            provider = FirewallProvider(platform)
        except ValueError:
            raise ValidationError(f"Unknown platform: {platform}")

        adapter = self._get_adapter(provider)
        if not adapter:
            return {
                "platform": platform,
                "configured": False,
                "status": "not_configured",
                "message": "No configuration found for this platform",
            }

        # Check database config
        config = self.db.query(FirewallProviderConfig).filter(
            FirewallProviderConfig.provider == provider
        ).first()

        return {
            "platform": platform,
            "configured": True,
            "status": config.health_status if config else "unknown",
            "simulation_mode": adapter.get("simulation_mode", True),
            "requires_approval": adapter.get("requires_approval", True),
            "last_health_check": config.last_health_check.isoformat() if config and config.last_health_check else None,
            "health_error": config.health_error if config else None,
        }

    def test_platform_connection(self, platform: str, config: dict) -> dict:
        """Test connection to a firewall platform."""
        try:
            provider = FirewallProvider(platform)
        except ValueError:
            raise ValidationError(f"Unknown platform: {platform}")

        # This would test actual connection in production
        # For now, return a simulated response
        return {
            "platform": platform,
            "success": True,
            "message": f"Connection test successful for {platform} (simulated)",
            "latency_ms": 42,
            "details": {
                "version": "1.0.0",
                "capabilities": ["ingress", "egress", "logging"],
            },
        }

    # =========================================================
    # Helper Methods
    # =========================================================

    def _generate_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate platform-specific commands for a rule."""
        commands = []
        
        if rule.provider == FirewallProvider.WINDOWS_FIREWALL:
            commands = self._generate_windows_commands(rule, operation)
        elif rule.provider == FirewallProvider.UFW:
            commands = self._generate_ufw_commands(rule, operation)
        elif rule.provider == FirewallProvider.IPTABLES:
            commands = self._generate_iptables_commands(rule, operation)
        elif rule.provider == FirewallProvider.PFSENSE:
            commands = self._generate_pfsense_commands(rule, operation)
        elif rule.provider in [FirewallProvider.AWS_SECURITY_GROUP, FirewallProvider.AZURE_NSG, FirewallProvider.GCP_FIREWALL]:
            commands = self._generate_cloud_commands(rule, operation)
        else:
            commands = [{"error": f"Provider {rule.provider.value} not implemented"}]

        return commands

    def _generate_windows_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate Windows Firewall netsh commands."""
        commands = []
        action = "block" if rule.action == FirewallAction.BLOCK else "allow"
        direction = "in" if rule.direction in ["inbound", "both"] else "out"
        
        if operation == "apply":
            cmd = f'netsh advfirewall firewall add rule name="{rule.name}" dir={direction} action={action}'
            if rule.source_ip:
                cmd += f' remoteip={rule.source_ip}'
            if rule.destination_ip:
                cmd += f' localip={rule.destination_ip}'
            if rule.protocol:
                cmd += f' protocol={rule.protocol}'
            if rule.destination_port:
                cmd += f' localport={rule.destination_port}'
            if rule.source_port:
                cmd += f' remoteport={rule.source_port}'
            cmd += f' description="AI_SOC:{rule.rule_id}"'
            commands.append({"command": cmd, "type": "netsh"})
        else:  # rollback
            cmd = f'netsh advfirewall firewall delete rule name="{rule.name}"'
            commands.append({"command": cmd, "type": "netsh"})

        if rule.direction == "both":
            # Add outbound rule
            if operation == "apply":
                cmd = f'netsh advfirewall firewall add rule name="{rule.name}_out" dir=out action={action}'
                if rule.source_ip:
                    cmd += f' localip={rule.source_ip}'
                if rule.destination_ip:
                    cmd += f' remoteip={rule.destination_ip}'
                if rule.protocol:
                    cmd += f' protocol={rule.protocol}'
                if rule.destination_port:
                    cmd += f' remoteport={rule.destination_port}'
                if rule.source_port:
                    cmd += f' localport={rule.source_port}'
                cmd += f' description="AI_SOC:{rule.rule_id}"'
                commands.append({"command": cmd, "type": "netsh"})
            else:
                cmd = f'netsh advfirewall firewall delete rule name="{rule.name}_out"'
                commands.append({"command": cmd, "type": "netsh"})

        return commands

    def _generate_ufw_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate UFW commands."""
        commands = []
        action = "deny" if rule.action == FirewallAction.BLOCK else "allow"
        direction = "from" if rule.direction in ["inbound", "both"] else "to"
        
        if operation == "apply":
            cmd = f"ufw {action} {direction} {rule.source_ip or 'any'}"
            if rule.destination_port:
                cmd += f" port {rule.destination_port}"
            if rule.protocol:
                cmd += f" proto {rule.protocol}"
            cmd += f' comment "AI_SOC:{rule.rule_id}"'
            commands.append({"command": cmd, "type": "ufw"})
        else:
            # UFW delete by rule number - would need to find rule number first
            cmd = f"ufw delete {action} {direction} {rule.source_ip or 'any'}"
            if rule.destination_port:
                cmd += f" port {rule.destination_port}"
            if rule.protocol:
                cmd += f" proto {rule.protocol}"
            commands.append({"command": cmd, "type": "ufw"})

        return commands

    def _generate_iptables_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate iptables commands."""
        commands = []
        chain = "INPUT" if rule.direction in ["inbound", "both"] else "OUTPUT"
        action = "DROP" if rule.action == FirewallAction.BLOCK else "ACCEPT"
        
        if operation == "apply":
            cmd = f"iptables -A {chain} -j {action}"
            if rule.source_ip:
                cmd += f" -s {rule.source_ip}"
            if rule.destination_ip:
                cmd += f" -d {rule.destination_ip}"
            if rule.protocol and rule.protocol != "any":
                cmd += f" -p {rule.protocol}"
            if rule.destination_port:
                cmd += f" --dport {rule.destination_port}"
            if rule.source_port:
                cmd += f" --sport {rule.source_port}"
            cmd += f' -m comment --comment "AI_SOC:{rule.rule_id}"'
            commands.append({"command": cmd, "type": "iptables"})
        else:
            # Delete rule - use -D with same parameters
            cmd = f"iptables -D {chain} -j {action}"
            if rule.source_ip:
                cmd += f" -s {rule.source_ip}"
            if rule.destination_ip:
                cmd += f" -d {rule.destination_ip}"
            if rule.protocol and rule.protocol != "any":
                cmd += f" -p {rule.protocol}"
            if rule.destination_port:
                cmd += f" --dport {rule.destination_port}"
            if rule.source_port:
                cmd += f" --sport {rule.source_port}"
            cmd += f' -m comment --comment "AI_SOC:{rule.rule_id}"'
            commands.append({"command": cmd, "type": "iptables"})

        return commands

    def _generate_pfsense_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate pfSense API commands."""
        # pfSense uses REST API - return API payload
        action = "block" if rule.action == FirewallAction.BLOCK else "pass"
        direction = "in" if rule.direction in ["inbound", "both"] else "out"
        
        payload = {
            "rule": {
                "action": action,
                "interface": "wan" if direction == "in" else "lan",
                "direction": direction,
                "protocol": rule.protocol or "any",
                "source": {"address": rule.source_ip or "any"},
                "destination": {"address": rule.destination_ip or "any"},
                "descr": f"AI_SOC:{rule.rule_id}",
            }
        }
        
        if rule.destination_port:
            payload["rule"]["destination"]["port"] = str(rule.destination_port)
        if rule.source_port:
            payload["rule"]["source"]["port"] = str(rule.source_port)

        if operation == "apply":
            return [{"method": "POST", "endpoint": "/api/v1/firewall/rule", "payload": payload, "type": "pfsense_api"}]
        else:
            # Would need rule ID to delete
            return [{"method": "DELETE", "endpoint": f"/api/v1/firewall/rule/{rule.provider_rule_id}", "type": "pfsense_api"}]

    def _generate_cloud_commands(self, rule: FirewallRule, operation: str) -> list[dict]:
        """Generate cloud provider commands (AWS, Azure, GCP)."""
        # Return API payload for cloud providers
        action = "deny" if rule.action == FirewallAction.BLOCK else "allow"
        
        payload = {
            "rule": {
                "action": action,
                "direction": "ingress" if rule.direction in ["inbound", "both"] else "egress",
                "protocol": rule.protocol or "any",
                "source": rule.source_ip or "0.0.0.0/0",
                "destination": rule.destination_ip or "0.0.0.0/0",
                "description": f"AI_SOC:{rule.rule_id}",
            }
        }
        
        if rule.destination_port:
            payload["rule"]["destination_port"] = rule.destination_port
        if rule.source_port:
            payload["rule"]["source_port"] = rule.source_port

        if operation == "apply":
            return [{"method": "POST", "endpoint": "/security-groups/rules", "payload": payload, "type": f"{rule.provider.value}_api"}]
        else:
            return [{"method": "DELETE", "endpoint": f"/security-groups/rules/{rule.provider_rule_id}", "type": f"{rule.provider.value}_api"}]

    def _execute_commands(self, adapter: dict, commands: list[dict], simulation_mode: bool) -> dict:
        """Execute commands on the target platform."""
        results = []
        overall_success = True

        for cmd in commands:
            if simulation_mode:
                results.append({
                    "command": cmd,
                    "success": True,
                    "output": f"[SIMULATION] Would execute: {cmd.get('command', cmd)}",
                    "simulated": True,
                })
                continue

            # In production, execute actual commands based on adapter type
            # This is a placeholder for actual implementation
            try:
                adapter_type = adapter.get("provider", "unknown")
                if adapter_type == "windows_firewall":
                    # Would use subprocess to run netsh
                    output = "Windows Firewall rule applied (placeholder)"
                elif adapter_type in ["ufw", "iptables"]:
                    # Would use subprocess to run ufw/iptables
                    output = f"{adapter_type} rule applied (placeholder)"
                elif adapter_type == "pfsense":
                    # Would use requests to call pfSense API
                    output = "pfSense rule applied via API (placeholder)"
                elif adapter_type in ["aws_security_group", "azure_nsg", "gcp_firewall"]:
                    # Would use cloud SDK (boto3, azure-mgmt, google-cloud)
                    output = f"{adapter_type} rule applied via SDK (placeholder)"
                else:
                    output = "Rule applied (placeholder)"

                results.append({
                    "command": cmd,
                    "success": True,
                    "output": output,
                    "simulated": False,
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "success": False,
                    "error": str(e),
                    "simulated": False,
                })
                overall_success = False

        return {
            "success": overall_success,
            "results": results,
            "message": "All commands executed successfully" if overall_success else "Some commands failed",
            "provider_rule_id": f"ext_{uuid4().hex[:12]}" if overall_success else None,
        }

    def _check_overlapping_rules(self, rule: FirewallRule) -> list[FirewallRule]:
        """Check for overlapping rules."""
        query = self.db.query(FirewallRule).filter(
            FirewallRule.id != rule.id,
            FirewallRule.provider == rule.provider,
            FirewallRule.status == FirewallRuleStatus.ACTIVE,
            FirewallRule.enabled == True,
        )

        # Check for IP overlap
        if rule.source_ip:
            query = query.filter(
                or_(
                    FirewallRule.source_ip == rule.source_ip,
                    FirewallRule.source_ips.contains([rule.source_ip]),
                )
            )

        return query.limit(10).all()

    def _create_audit_log(
        self,
        rule_id: UUID,
        user_id: UUID,
        action: str,
        previous_status: Optional[FirewallRuleStatus] = None,
        new_status: Optional[FirewallRuleStatus] = None,
        details: Optional[dict] = None,
        execution_time_ms: Optional[int] = None,
        provider_response: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> FirewallAuditLog:
        """Create an audit log entry."""
        audit = FirewallAuditLog(
            rule_id=rule_id,
            user_id=user_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            details=details,
            execution_time_ms=execution_time_ms,
            provider_response=provider_response,
            error_message=error_message,
        )
        self.db.add(audit)
        self.db.commit()
        return audit

    # =========================================================
    # Maintenance
    # =========================================================

    def cleanup_expired_rules(self) -> dict:
        """Clean up expired firewall rules."""
        now = datetime.now(timezone.utc)
        expired_rules = self.db.query(FirewallRule).filter(
            FirewallRule.expires_at.isnot(None),
            FirewallRule.expires_at <= now,
            FirewallRule.status.in_([FirewallRuleStatus.ACTIVE, FirewallRuleStatus.SIMULATED]),
        ).all()

        cleaned = 0
        errors = []

        for rule in expired_rules:
            try:
                # Create a system user for cleanup
                system_user = UUID(int=0)
                exec_request = FirewallExecutionRequest(simulation_mode=rule.is_simulation, reason="Automatic cleanup of expired rule")
                self.rollback_rule(rule.id, exec_request, system_user)
                cleaned += 1
            except Exception as e:
                errors.append(f"Failed to cleanup rule {rule.rule_id}: {e}")

        return {
            "cleaned": cleaned,
            "errors": errors,
        }

    def get_audit_logs(
        self,
        rule_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FirewallAuditLog], int]:
        """Get firewall audit logs."""
        query = self.db.query(FirewallAuditLog)

        if rule_id:
            query = query.filter(FirewallAuditLog.rule_id == rule_id)
        if user_id:
            query = query.filter(FirewallAuditLog.user_id == user_id)
        if action:
            query = query.filter(FirewallAuditLog.action == action)

        total = query.count()
        logs = query.order_by(desc(FirewallAuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        return logs, total