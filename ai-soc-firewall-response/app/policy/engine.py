from pydantic import BaseModel
from typing import Optional

class PolicyRule(BaseModel):
    id: str
    name: str
    condition: dict
    action: str
    duration_minutes: int = 30
    enabled: bool = True

class ResponsePolicy(BaseModel):
    rule_id: str
    action: str
    target_ip: str
    duration_minutes: int
    analyst_approval_required: bool = True
    metadata: dict = {}

class PolicyEngine:
    """Deterministic response-policy engine."""
    
    def __init__(self):
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default security response rules."""
        return [
            PolicyRule(
                id="rule-1",
                name="DoS Attack Detection",
                condition={"attack_type": "DoS", "severity": "Critical"},
                action="block_ip",
                duration_minutes=30
            ),
            PolicyRule(
                id="rule-2", 
                name="Suspicious Scanning",
                condition={"attack_type": "SCAN", "severity": "Medium"},
                action="block_ip",
                duration_minutes=15
            ),
            PolicyRule(
                id="rule-3",
                name="High Severity Threat",
                condition={"severity": "High"},
                action="block_ip",
                duration_minutes=60
            )
        ]
    
    def evaluate(self, alert_data: dict) -> Optional[ResponsePolicy]:
        """Evaluate alert against policy rules and return response decision."""
        for rule in self.rules:
            condition = rule.condition
            if (alert_data.get("attack_type") == condition.get("attack_type") and
                alert_data.get("severity") == condition.get("severity")):
                return ResponsePolicy(
                    rule_id=rule.id,
                    action=rule.action,
                    target_ip=alert_data.get("source_ip", ""),
                    duration_minutes=rule.duration_minutes,
                    analyst_approval_required=True
                )
        return None