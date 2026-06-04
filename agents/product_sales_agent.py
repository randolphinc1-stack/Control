"""Agent for managing product sales and deal creation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from .base_agent import BaseAgent


class ProductTier(Enum):
    """Product pricing tiers."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DealStatus(Enum):
    """Deal status in the sales pipeline."""
    PROPOSAL_SENT = "proposal_sent"
    UNDER_REVIEW = "under_review"
    NEGOTIATING = "negotiating"
    READY_TO_CLOSE = "ready_to_close"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ProductSalesAgent(BaseAgent):
    """Agent for managing product sales and deal tracking."""

    def __init__(self, agent_id: str = "sales_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the product sales agent."""
        super().__init__(agent_id, "Product Sales Agent", config)
        self.products: Dict[str, Dict[str, Any]] = {}
        self.deals: Dict[str, Dict[str, Any]] = {}
        self._initialize_products()

    def _initialize_products(self) -> None:
        """Initialize default product catalog."""
        self.products = {
            "BASIC": {
                "product_id": "BASIC",
                "name": "Basic Package",
                "description": "Entry-level solution for small businesses",
                "tier": ProductTier.BASIC.value,
                "price": 29.99,
                "features": [
                    "Core functionality",
                    "Email support",
                    "Up to 100 users",
                ],
                "billing_cycle": "monthly",
            },
            "PROFESSIONAL": {
                "product_id": "PROFESSIONAL",
                "name": "Professional Package",
                "description": "Mid-tier solution for growing businesses",
                "tier": ProductTier.PROFESSIONAL.value,
                "price": 99.99,
                "features": [
                    "Advanced features",
                    "Priority email/phone support",
                    "Up to 500 users",
                    "Custom integrations",
                ],
                "billing_cycle": "monthly",
            },
            "ENTERPRISE": {
                "product_id": "ENTERPRISE",
                "name": "Enterprise Package",
                "description": "Full-featured solution for large organizations",
                "tier": ProductTier.ENTERPRISE.value,
                "price": 299.99,
                "features": [
                    "All features",
                    "24/7 phone support",
                    "Unlimited users",
                    "Custom development",
                    "Dedicated account manager",
                ],
                "billing_cycle": "monthly",
            },
        }

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute product sales logic.

        Args:
            context: Contains action and related parameters

        Returns:
            Operation result
        """
        try:
            self.start_session()
            
            action = context.get("action", "get_products")
            
            if action == "get_products":
                result = self.get_products()
            elif action == "recommend_product":
                result = self.recommend_product(context)
            elif action == "create_deal":
                result = self.create_deal(context)
            elif action == "update_deal":
                result = self.update_deal(context.get("deal_id"), context)
            elif action == "generate_proposal":
                result = self.generate_proposal(context)
            elif action == "get_deal":
                result = self.get_deal(context.get("deal_id"))
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.end_session(success=True)
            return result
            
        except Exception as e:
            return self.handle_error(e, context)

    def get_products(self) -> Dict[str, Any]:
        """
        Get all available products.

        Returns:
            Product catalog
        """
        return {
            "success": True,
            "count": len(self.products),
            "products": list(self.products.values()),
        }

    def recommend_product(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend a product based on lead criteria.

        Args:
            context: Lead information (company_size, budget, features_needed)

        Returns:
            Product recommendation
        """
        company_size = context.get("company_size", "small")
        budget = context.get("budget", 0)
        features_needed = context.get("features_needed", [])

        recommendation = None
        score_map = {}

        for product in self.products.values():
            score = 0
            
            # Size-based scoring
            if company_size == "small" and product["tier"] == ProductTier.BASIC.value:
                score += 30
            elif company_size == "medium" and product["tier"] == ProductTier.PROFESSIONAL.value:
                score += 30
            elif company_size == "large" and product["tier"] == ProductTier.ENTERPRISE.value:
                score += 30
            
            # Budget-based scoring
            if budget > 0:
                if product["price"] <= budget:
                    score += 20
                elif product["price"] <= budget * 1.5:
                    score += 10
            
            # Feature matching
            matching_features = sum(
                1 for feature in features_needed 
                if any(f.lower() in feature.lower() for f in product["features"])
            )
            score += matching_features * 10

            score_map[product["product_id"]] = score

        if score_map:
            best_product_id = max(score_map, key=score_map.get)
            recommendation = self.products[best_product_id]

        self.log_action("recommend_product", {
            "company_size": company_size,
            "budget": budget,
            "scores": score_map,
        })

        return {
            "success": True,
            "recommendation": recommendation,
            "scores": score_map,
        }

    def create_deal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a sales deal.

        Args:
            context: Deal information (lead_id, product_id, discount_percent)

        Returns:
            Created deal
        """
        required_fields = ["lead_id", "product_id"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        product_id = context["product_id"]
        if product_id not in self.products:
            return {"success": False, "error": f"Product {product_id} not found"}

        deal_id = self._generate_deal_id()
        product = self.products[product_id]
        
        # Calculate pricing with discount
        discount_percent = context.get("discount_percent", 0)
        discount_amount = (product["price"] * discount_percent) / 100
        final_price = product["price"] - discount_amount

        deal = {
            "deal_id": deal_id,
            "lead_id": context["lead_id"],
            "product_id": product_id,
            "product_name": product["name"],
            "status": DealStatus.PROPOSAL_SENT.value,
            "list_price": product["price"],
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "final_price": final_price,
            "billing_cycle": product["billing_cycle"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "proposal_valid_until": context.get("proposal_valid_until", "2026-06-11"),
            "notes": context.get("notes", ""),
        }

        self.deals[deal_id] = deal

        self.log_action("create_deal", {
            "deal_id": deal_id,
            "lead_id": context["lead_id"],
            "product_id": product_id,
            "final_price": final_price,
        })

        return {
            "success": True,
            "deal_id": deal_id,
            "deal": deal,
        }

    def update_deal(self, deal_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a sales deal.

        Args:
            deal_id: ID of deal to update
            context: Updated deal information

        Returns:
            Updated deal
        """
        if deal_id not in self.deals:
            return {"success": False, "error": f"Deal {deal_id} not found"}

        deal = self.deals[deal_id]

        # Update allowed fields
        if "status" in context and context["status"] in [s.value for s in DealStatus]:
            deal["status"] = context["status"]
        
        if "notes" in context:
            deal["notes"] = context["notes"]
        
        if "discount_percent" in context:
            discount_percent = context["discount_percent"]
            deal["discount_percent"] = discount_percent
            deal["discount_amount"] = (deal["list_price"] * discount_percent) / 100
            deal["final_price"] = deal["list_price"] - deal["discount_amount"]

        deal["updated_at"] = datetime.now().isoformat()

        self.log_action("update_deal", {
            "deal_id": deal_id,
            "status": deal["status"],
        })

        return {
            "success": True,
            "deal_id": deal_id,
            "deal": deal,
        }

    def generate_proposal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a sales proposal for a deal.

        Args:
            context: Contains deal_id

        Returns:
            Generated proposal text
        """
        deal_id = context.get("deal_id")
        if deal_id not in self.deals:
            return {"success": False, "error": f"Deal {deal_id} not found"}

        deal = self.deals[deal_id]
        product = self.products[deal["product_id"]]

        proposal = f"""
=== SALES PROPOSAL ===

Deal ID: {deal_id}
Lead ID: {deal["lead_id"]}
Date: {datetime.now().strftime('%Y-%m-%d')}

PRODUCT: {product['name']}
DESCRIPTION: {product['description']}

FEATURES:
{chr(10).join(f'• {f}' for f in product['features'])}

PRICING:
• List Price: ${deal['list_price']:.2f}
• Discount: {deal['discount_percent']}% (${deal['discount_amount']:.2f})
• Final Price: ${deal['final_price']:.2f}
• Billing Cycle: {deal['billing_cycle']}

TERMS:
• Valid Until: {deal['proposal_valid_until']}
• Status: {deal['status']}

NOTES:
{deal['notes']}

---
Please review and contact us if you have any questions.
"""

        self.log_action("generate_proposal", {"deal_id": deal_id})

        return {
            "success": True,
            "deal_id": deal_id,
            "proposal": proposal,
        }

    def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """
        Get deal information.

        Args:
            deal_id: ID of deal

        Returns:
            Deal data
        """
        if deal_id not in self.deals:
            return {"success": False, "error": f"Deal {deal_id} not found"}

        return {
            "success": True,
            "deal": self.deals[deal_id],
        }

    def get_deals_by_status(self, status: str) -> Dict[str, Any]:
        """
        Get all deals with a specific status.

        Args:
            status: Deal status to filter by

        Returns:
            List of deals with given status
        """
        deals = [d for d in self.deals.values() if d["status"] == status]
        return {
            "success": True,
            "status": status,
            "count": len(deals),
            "deals": deals,
        }

    def _generate_deal_id(self) -> str:
        """Generate a unique deal ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        deal_count = len(self.deals) + 1
        return f"DEAL_{timestamp}_{deal_count:05d}"
