from datetime import datetime, timezone

from backend.models.schemas import Incident


class IncidentService:
    """Incident lifecycle management for the SOC."""

    LIFECYCLE_STATES = [
        "new",
        "investigating",
        "contained",
        "eradicated",
        "recovered",
        "closed",
    ]

    @staticmethod
    def validate_state_transition(from_state: str, to_state: str) -> bool:
        """Validate that a state transition is allowed in the incident lifecycle."""
        if from_state not in IncidentService.LIFECYCLE_STATES or to_state not in IncidentService.LIFECYCLE_STATES:
            return False

        # Define allowed transitions
        allowed_transitions = {
            "new": ["investigating"],
            "investigating": ["contained", "investigating"],  # can loop during investigation
            "contained": ["eradicated"],
            "eradicated": ["recovered"],
            "recovered": ["closed"],
            "closed": [],  # terminal state
        }

        return to_state in allowed_transitions.get(from_state, [])

    @staticmethod
    def create_incident(attack_data: dict, source_ip: str, severity: str = "medium") -> dict:
        """
        Create a new incident from a detected attack.

        Args:
            attack_data: dict with attack details
            source_ip: The source IP that triggered the incident
            severity: Incident severity (low, medium, high, critical)

        Returns:
            dict with incident details including incident_id
        """
        incident_id = f"inc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{attack_data.get('id', 'unknown')}"

        incident = {
            "incident_id": incident_id,
            "title": f"Security incident from {source_ip}",
            "description": f"Automatically generated incident from attack detection: {attack_data.get('attack_type', 'unknown')}",
            "source_ip": source_ip,
            "severity": severity,
            "status": "new",
            "lifecycle_state": "new",
            "assigned_to": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "closed_at": None,
            "mitre_technique": attack_data.get("mitre_technique"),
            "mitre_tactic": attack_data.get("mitre_tactic"),
            "risk_score": attack_data.get("risk_score", 50),
            "evidence": [],
            "timeline: [],
            "root_cause: None,
            "remediation: None,
            tags: [attack_data.get("attack_type", "unknown")],
        }

        # Store incident (in production, would insert into database)
        # DBService.insert_incident(incident)

        return {"incident": incident, "message": f"Incident {incident_id} created successfully"}

    @staticmethod
    def update_incident(
        incident_id: str,
        lifecycle_state: str = None,
        status: str = None,
        assigned_to: str = None,
        evidence: list = None,
        timeline: list = None,
        root_cause: str = None,
        remediation: str = None,
    ) -> dict:
        """
        Update an incident with new state or information.

        Args:
            incident_id: The incident ID to update
            lifecycle_state: New lifecycle state (validated transition)
            status: New status
            assigned_to: Analyst to assign to
            evidence: New evidence to add
            timeline: New timeline entries to add
            root_cause: Root cause analysis
            remediation: Remediation actions taken

        Returns:
            dict with update result
        """
        # In production, would fetch from database and update
        # For now, return structure

        update_log = []

        if lifecycle_state:
            if IncidentService.validate_state_transition(
                # Would fetch current state from DB
                "new",  # Placeholder - would use current state
                lifecycle_state,
            ):
                update_log.append(f"state: {lifecycle_state}")
                # Would update incident.lifecycle_state = lifecycle_state

        if status:
            update_log.append(f"status: {status}")

        if assigned_to is not None:
            update_log.append(f"assigned_to: {assigned_to}")

        if evidence:
            update_log.append(f"evidence added: {len(evidence)} new items")

        if timeline:
            update_log.append(f"timeline entries added: {len(timeline)}")

        if root_cause:
            update_log.append(f"root_cause updated")

        if remediation:
            update_log.append(f"remediation updated")

        return {
            "incident_id": incident_id,
            "updated_fields": update_log,
            "message": f"Incident {incident_id} updated",
        }

    @staticmethod
    def assign_incident(incident_id: str, analyst_id: str) -> dict:
        """Assign an incident to an analyst."""
        return {
            "incident_id": incident_id,
            "assigned_to": analyst_id,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Incident {incident_id} assigned to analyst {analyst_id}",
        }

    @staticmethod
    def close_incident(incident_id: str, final_status: str = "closed", summary: str = "") -> dict:
        """
        Close an incident with a summary.

        Args:
            incident_id: The incident ID to close
            final_status: Final status (typically 'closed')
            summary: Optional summary of the incident resolution

        Returns:
            dict with close result
        """
        return {
            "incident_id": incident_id,
            "final_status": final_status,
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary or "Incident resolved",
            "message": f"Incident {incident_id} closed successfully",
        }