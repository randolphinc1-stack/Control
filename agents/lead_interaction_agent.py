"""Agent for managing lead interactions and communications."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from .base_agent import BaseAgent


class LeadStatus(Enum):
    """Lead status in the sales pipeline."""
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DORMANT = "dormant"


class LeadInteractionAgent(BaseAgent):
    """Agent for managing lead interactions and relationship tracking."""

    def __init__(self, agent_id: str = "lead_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the lead interaction agent."""
        super().__init__(agent_id, "Lead Interaction Agent", config)
        self.leads: Dict[str, Dict[str, Any]] = {}
        self.interactions: Dict[str, List[Dict[str, Any]]] = {}

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute lead interaction logic.

        Args:
            context: Contains lead_id and action (create, update, log_interaction)

        Returns:
            Operation result
        """
        try:
            self.start_session()
            
            action = context.get("action", "log_interaction")
            lead_id = context.get("lead_id")
            
            if action == "create":
                result = self.create_lead(context)
            elif action == "update":
                result = self.update_lead(lead_id, context)
            elif action == "log_interaction":
                result = self.log_interaction(lead_id, context)
            elif action == "qualify_lead":
                result = self.qualify_lead(lead_id)
            elif action == "get_lead":
                result = self.get_lead(lead_id)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.end_session(success=True)
            return result
            
        except Exception as e:
            return self.handle_error(e, context)

    def create_lead(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lead record.

        Args:
            context: Lead information (name, email, phone, source)

        Returns:
            Created lead data
        """
        required_fields = ["name", "email", "phone"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        lead_id = self._generate_lead_id()
        
        lead = {
            "lead_id": lead_id,
            "name": context["name"],
            "email": context["email"],
            "phone": context["phone"],
            "source": context.get("source", "unknown"),
            "company": context.get("company", ""),
            "status": LeadStatus.NEW.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "lead_score": 0,
            "custom_data": context.get("custom_data", {}),
        }
        
        self.leads[lead_id] = lead
        self.interactions[lead_id] = []
        
        self.log_action("create_lead", {"lead_id": lead_id, "name": context["name"]})
        
        return {
            "success": True,
            "lead_id": lead_id,
            "lead": lead,
        }

    def update_lead(self, lead_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing lead record.

        Args:
            lead_id: ID of lead to update
            context: Updated lead information

        Returns:
            Updated lead data
        """
        if lead_id not in self.leads:
            return {"success": False, "error": f"Lead {lead_id} not found"}

        lead = self.leads[lead_id]
        
        # Update allowed fields
        updatable_fields = ["email", "phone", "company", "status", "custom_data"]
        for field in updatable_fields:
            if field in context:
                if field == "status" and context[field] in [s.value for s in LeadStatus]:
                    lead[field] = context[field]
                elif field != "status":
                    lead[field] = context[field]

        lead["updated_at"] = datetime.now().isoformat()
        
        self.log_action("update_lead", {"lead_id": lead_id})
        
        return {
            "success": True,
            "lead_id": lead_id,
            "lead": lead,
        }

    def log_interaction(self, lead_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an interaction with a lead.

        Args:
            lead_id: ID of lead
            context: Interaction details (type, notes, outcome)

        Returns:
            Logged interaction
        """
        if lead_id not in self.leads:
            return {"success": False, "error": f"Lead {lead_id} not found"}

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": context.get("type", "call"),  # call, email, meeting, etc.
            "notes": context.get("notes", ""),
            "outcome": context.get("outcome", "neutral"),  # positive, negative, neutral
            "duration_minutes": context.get("duration_minutes", 0),
            "next_action": context.get("next_action", ""),
        }

        self.interactions[lead_id].append(interaction)
        
        # Update lead's updated_at and status if provided
        self.leads[lead_id]["updated_at"] = datetime.now().isoformat()
        if context.get("new_status"):
            self.leads[lead_id]["status"] = context["new_status"]
        
        self.log_action("log_interaction", {"lead_id": lead_id, "type": interaction["type"]})
        
        return {
            "success": True,
            "interaction": interaction,
        }

    def qualify_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Qualify a lead based on interaction history and engagement.

        Args:
            lead_id: ID of lead to qualify

        Returns:
            Lead qualification result
        """
        if lead_id not in self.leads:
            return {"success": False, "error": f"Lead {lead_id} not found"}

        lead = self.leads[lead_id]
        interactions = self.interactions.get(lead_id, [])
        
        # Calculate lead score
        score = 0
        score += len(interactions) * 10  # 10 points per interaction
        
        # Bonus for positive interactions
        positive_interactions = sum(1 for i in interactions if i["outcome"] == "positive")
        score += positive_interactions * 20
        
        # Check for recent activity
        if interactions:
            last_interaction = interactions[-1]
            last_date = datetime.fromisoformat(last_interaction["timestamp"])
            days_since = (datetime.now() - last_date).days
            if days_since < 7:
                score += 15
        
        lead["lead_score"] = score
        
        # Determine if qualified
        is_qualified = score >= 30
        if is_qualified and lead["status"] == LeadStatus.NEW.value:
            lead["status"] = LeadStatus.QUALIFIED.value
        
        self.log_action("qualify_lead", {"lead_id": lead_id, "score": score})
        
        return {
            "success": True,
            "lead_id": lead_id,
            "lead_score": score,
            "is_qualified": is_qualified,
            "lead": lead,
        }

    def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Get lead information with full interaction history.

        Args:
            lead_id: ID of lead

        Returns:
            Lead data and interactions
        """
        if lead_id not in self.leads:
            return {"success": False, "error": f"Lead {lead_id} not found"}

        return {
            "success": True,
            "lead": self.leads[lead_id],
            "interactions": self.interactions.get(lead_id, []),
        }

    def get_leads_by_status(self, status: str) -> Dict[str, Any]:
        """
        Get all leads with a specific status.

        Args:
            status: Lead status to filter by

        Returns:
            List of leads with given status
        """
        leads = [l for l in self.leads.values() if l["status"] == status]
        return {
            "success": True,
            "status": status,
            "count": len(leads),
            "leads": leads,
        }

    def get_all_leads(self) -> Dict[str, Any]:
        """
        Get all leads.

        Returns:
            List of all leads
        """
        return {
            "success": True,
            "count": len(self.leads),
            "leads": list(self.leads.values()),
        }

    def _generate_lead_id(self) -> str:
        """Generate a unique lead ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        lead_count = len(self.leads) + 1
        return f"LEAD_{timestamp}_{lead_count:05d}"
