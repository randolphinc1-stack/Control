"""Main orchestrator for coordinating all sales agents."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from .lead_interaction_agent import LeadInteractionAgent
from .product_sales_agent import ProductSalesAgent
from .phone_call_agent import PhoneCallAgent
from .payment_agent import PaymentAgent


class SalesOrchestrator:
    """Orchestrates all sales agents to automate the complete sales pipeline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sales orchestrator with all agents.

        Args:
            config: Configuration dictionary for all agents
        """
        self.config = config or {}
        self.logger = logging.getLogger("SalesOrchestrator")
        
        # Initialize all agents
        self.lead_agent = LeadInteractionAgent(config=self.config)
        self.sales_agent = ProductSalesAgent(config=self.config)
        self.call_agent = PhoneCallAgent(config=self.config)
        self.payment_agent = PaymentAgent(config=self.config)
        
        self.agents = {
            "lead": self.lead_agent,
            "sales": self.sales_agent,
            "call": self.call_agent,
            "payment": self.payment_agent,
        }
        
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.logger.info("Sales Orchestrator initialized")

    def process_lead(self, phone: str, email: str, name: str, source: str = "unknown") -> Dict[str, Any]:
        """
        Process a new lead through the system.

        Args:
            phone: Lead phone number
            email: Lead email address
            name: Lead name
            source: Lead source (web, phone, referral, etc.)

        Returns:
            Lead processing result
        """
        self.logger.info(f"Processing lead: {name} ({email})")
        
        # Create lead in the system
        lead_result = self.lead_agent.execute({
            "action": "create",
            "name": name,
            "email": email,
            "phone": phone,
            "source": source,
        })

        if not lead_result.get("success"):
            return {"success": False, "error": "Failed to create lead"}

        lead_id = lead_result["lead_id"]

        # Log initial interaction
        self.lead_agent.execute({
            "action": "log_interaction",
            "lead_id": lead_id,
            "type": "incoming_lead",
            "notes": f"Lead received from {source}",
            "outcome": "positive",
        })

        # Get product recommendations
        product_rec = self.sales_agent.execute({
            "action": "recommend_product",
            "company_size": "small",
            "budget": 100,
            "features_needed": [],
        })

        return {
            "success": True,
            "lead_id": lead_id,
            "lead": lead_result.get("lead"),
            "recommended_product": product_rec.get("recommendation"),
        }

    def handle_incoming_call(self, phone: str, lead_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle an incoming phone call.

        Args:
            phone: Caller phone number
            lead_id: Optional known lead ID

        Returns:
            Call handling result
        """
        self.logger.info(f"Incoming call from: {phone}")
        
        # If lead_id not provided, try to find lead by phone
        if not lead_id:
            leads = self.lead_agent.get_all_leads()
            for lead in leads.get("leads", []):
                if lead["phone"] == phone:
                    lead_id = lead["lead_id"]
                    break

        # Handle the call
        call_result = self.call_agent.execute({
            "action": "handle_inbound_call",
            "from_number": phone,
            "lead_id": lead_id or "",
        })

        if call_result.get("success"):
            # Auto-answer call
            self.call_agent.execute({
                "action": "answer_call",
                "call_id": call_result["call_id"],
            })

        return call_result

    def create_sales_deal(
        self,
        lead_id: str,
        product_id: str,
        discount_percent: float = 0,
    ) -> Dict[str, Any]:
        """
        Create a sales deal for a lead.

        Args:
            lead_id: ID of the lead
            product_id: Product to sell
            discount_percent: Discount percentage

        Returns:
            Deal creation result
        """
        self.logger.info(f"Creating deal for lead {lead_id}")
        
        # Verify lead exists
        lead = self.lead_agent.execute({
            "action": "get_lead",
            "lead_id": lead_id,
        })

        if not lead.get("success"):
            return {"success": False, "error": "Lead not found"}

        # Create the deal
        deal_result = self.sales_agent.execute({
            "action": "create_deal",
            "lead_id": lead_id,
            "product_id": product_id,
            "discount_percent": discount_percent,
        })

        if deal_result.get("success"):
            deal_id = deal_result["deal_id"]
            
            # Log interaction for the lead
            self.lead_agent.execute({
                "action": "log_interaction",
                "lead_id": lead_id,
                "type": "proposal",
                "notes": f"Proposal sent for {product_id}",
                "outcome": "positive",
            })

        return deal_result

    def process_payment(
        self,
        lead_id: str,
        deal_id: str,
        amount: float,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Process a payment for a deal.

        Args:
            lead_id: ID of the lead
            deal_id: ID of the deal
            amount: Payment amount
            payment_method: Payment method

        Returns:
            Payment result
        """
        self.logger.info(f"Processing payment for lead {lead_id}")
        
        # Process the payment
        payment_result = self.payment_agent.execute({
            "action": "process_payment",
            "lead_id": lead_id,
            "deal_id": deal_id,
            "amount": amount,
            "payment_method": payment_method,
        })

        if payment_result.get("success"):
            # Update deal status
            self.sales_agent.execute({
                "action": "update_deal",
                "deal_id": deal_id,
                "status": "closed_won",
            })

            # Log interaction
            self.lead_agent.execute({
                "action": "log_interaction",
                "lead_id": lead_id,
                "type": "payment",
                "notes": f"Payment received: ${amount}",
                "outcome": "positive",
                "new_status": "closed_won",
            })

            # Generate invoice
            invoice = self.payment_agent.execute({
                "action": "generate_invoice",
                "transaction_id": payment_result.get("transaction_id"),
                "lead_id": lead_id,
            })

            return {
                "success": True,
                "payment": payment_result,
                "invoice": invoice,
            }

        return payment_result

    def end_call(self, call_id: str, outcome: str, agent_notes: str = "") -> Dict[str, Any]:
        """
        End a call and log the interaction.

        Args:
            call_id: ID of call to end
            outcome: Call outcome
            agent_notes: Notes from the agent

        Returns:
            Call end result
        """
        self.logger.info(f"Ending call {call_id}")
        
        # Get call details
        call_status = self.call_agent.execute({
            "action": "get_call_status",
            "call_id": call_id,
        })

        if not call_status.get("success"):
            return {"success": False, "error": "Call not found"}

        # End the call
        end_result = self.call_agent.execute({
            "action": "end_call",
            "call_id": call_id,
            "outcome": outcome,
            "agent_notes": agent_notes,
        })

        # Log interaction if lead_id exists
        call_data = call_status.get("call", {})
        lead_id = call_data.get("lead_id")
        
        if lead_id:
            self.lead_agent.execute({
                "action": "log_interaction",
                "lead_id": lead_id,
                "type": "call",
                "notes": agent_notes,
                "outcome": outcome,
                "duration_minutes": call_data.get("duration_seconds", 0) // 60,
            })

        return end_result

    def get_lead_summary(self, lead_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a lead.

        Args:
            lead_id: ID of lead

        Returns:
            Lead summary with all interactions and deals
        """
        self.logger.info(f"Getting summary for lead {lead_id}")
        
        # Get lead info
        lead_result = self.lead_agent.execute({
            "action": "get_lead",
            "lead_id": lead_id,
        })

        if not lead_result.get("success"):
            return {"success": False, "error": "Lead not found"}

        lead = lead_result["lead"]
        interactions = lead_result["interactions"]

        # Get call history
        call_history = self.call_agent.get_call_history(lead_id)

        # Get deals for this lead
        all_deals = self.sales_agent.deals
        deals = [d for d in all_deals.values() if d.get("lead_id") == lead_id]

        return {
            "success": True,
            "lead_id": lead_id,
            "lead": lead,
            "interactions": interactions,
            "calls": call_history.get("calls", []),
            "deals": deals,
            "summary": {
                "total_interactions": len(interactions),
                "total_calls": len(call_history.get("calls", [])),
                "total_deals": len(deals),
                "lead_score": lead.get("lead_score", 0),
                "status": lead.get("status", "unknown"),
            },
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.

        Returns:
            System status report
        """
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "statistics": {
                "total_leads": len(self.lead_agent.leads),
                "total_calls": len(self.call_agent.calls),
                "active_calls": len(self.call_agent.active_calls),
                "total_deals": len(self.sales_agent.deals),
                "total_transactions": len(self.payment_agent.transactions),
            },
        }

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get a specific agent by name.

        Args:
            agent_name: Name of agent (lead, sales, call, payment)

        Returns:
            The agent instance
        """
        return self.agents.get(agent_name)
