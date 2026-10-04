#!/usr/bin/env python
"""SOC AI Assistant Service - Provides conversational AI access to SOC data."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pytz import timezone as pytz_timezone

from backend.core.security import get_current_user
from backend.database.mongodb import db
from backend.services.attack_service import AttackService
from backend.services.incident_service import IncidentService
from backend.services.firewall_service import FirewallService
from backend.services.threat_intel_service import ThreatIntelService
from backend.services.system_health import SystemHealth
from backend.services.db_service import DBService
from backend.ai_model import get_ai_pipeline


class SOCAssistant:
    def __init__(self):
        self.ai_pipeline = get_ai_pipeline()
        self.attack_service = AttackService()
        self.db_service = DBService()
        self.threat_intel_service = ThreatIntelService()
        self.system_health = SystemHealth()

    def _validate_query_input(self, query: str) -> bool:
        """Validate user query for prompt injection and malicious content."""
        if not query or not isinstance(query, str):
            return False
        injection_keywords = [
            'ignore previous', 'forget all', 'system prompt',
            'override instructions', '<<SYS>>', 'DO NOT',
            'PROMPT INJECTION', 'roleplay', 'hypothetical'
        ]
        query_lower = query.lower().strip()
        for keyword in injection_keywords:
            if keyword.lower() in query_lower:
                return False
        if len(query) > 500:
            return False
        substantive_terms = ['attack', 'incident', 'ip', 'threat', 'firewall',
                           'security', 'event', 'log', 'alert']
        has_substantive = any(term in query_lower for term in substantive_terms)
        if not has_substantive and len(query_lower) < 20:
            simple_terms = ['health', 'status', 'stat', 'stats']
            if not any(t in query_lower for t in simple_terms):
                return False
        return True

    def get_attack_summary(self, attack_type=None, severity=None, limit=50):
        try:
            if db() is None:
                return {"success": False, "error": "Database not connected"}
            filters = {}
            if attack_type:
                filters["attack_type"] = attack_type
            if severity:
                filters["severity"] = severity
            attack_collection = self.db_service.get_attack_collection()
            attacks = list(attack_collection.find(filters).sort("timestamp", -1).limit(max(limit, 1)))
            total_attacks = attack_collection.count_documents({})
            severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            attack_type_counts = {}
            risk_scores = []
            source_ips = set()
            for attack in attacks:
                sev = attack.get("severity", "low") or "low"
                if sev in severity_counts:
                    severity_counts[sev] += 1
                atype = attack.get("attack_type", "unknown") or "unknown"
                attack_type_counts[atype] = attack_type_counts.get(atype, 0) + 1
                risk_score = attack.get("risk_score", 0)
                if risk_score is not None:
                    try:
                        risk_scores.append(float(risk_score))
                    except (ValueError, TypeError):
                        pass
                source_ip = attack.get("source_ip", "") or ""
                if source_ip:
                    source_ips.add(source_ip)
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            return {
                "success": True,
                "total_attacks_in_database": total_attacks,
                "attacks_returned": len(attacks),
                "severity_breakdown": severity_counts,
                "attack_type_breakdown": attack_type_counts,
                "average_risk_score": round(avg_risk, 2),
                "unique_source_ips": len(source_ips),
                "filters_applied": {"attack_type": attack_type, "severity": severity},
                "timestamp": datetime.now(pytz_timezone("UTC")).isoformat()
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Failed to retrieve attack summary: {str(e)}",
                "traceback": traceback.format_exc() if len(traceback.format_exc()) < 500 else "Error occurred",
                "timestamp": datetime.now(pytz_timezone("UTC")).isoformat()
            }