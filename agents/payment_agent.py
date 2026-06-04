"""Agent for processing payments and transactions."""

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import hashlib
from .base_agent import BaseAgent


class PaymentStatus(Enum):
    """Payment transaction status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    """Supported payment methods."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CRYPTOCURRENCY = "cryptocurrency"


class PaymentAgent(BaseAgent):
    """Agent for processing payments and handling transactions."""

    def __init__(self, agent_id: str = "payment_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the payment processing agent."""
        super().__init__(agent_id, "Payment Agent", config)
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.refunds: Dict[str, Dict[str, Any]] = {}
        self.invoices: Dict[str, Dict[str, Any]] = {}

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute payment processing logic.

        Args:
            context: Contains action and payment parameters

        Returns:
            Operation result
        """
        try:
            self.start_session()
            
            action = context.get("action", "process_payment")
            
            if action == "process_payment":
                result = self.process_payment(context)
            elif action == "authorize_payment":
                result = self.authorize_payment(context)
            elif action == "capture_payment":
                result = self.capture_payment(context)
            elif action == "refund_payment":
                result = self.refund_payment(context)
            elif action == "generate_invoice":
                result = self.generate_invoice(context)
            elif action == "get_transaction":
                result = self.get_transaction(context.get("transaction_id"))
            elif action == "get_payment_methods":
                result = self.get_payment_methods()
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.end_session(success=True)
            return result
            
        except Exception as e:
            return self.handle_error(e, context)

    def process_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment transaction.

        Args:
            context: Payment details (lead_id, deal_id, amount, payment_method, card_token)

        Returns:
            Payment result
        """
        required_fields = ["lead_id", "amount", "payment_method"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        transaction_id = self._generate_transaction_id()
        
        # Validate amount
        amount = float(context["amount"])
        if amount <= 0:
            return {"success": False, "error": "Invalid amount"}

        transaction = {
            "transaction_id": transaction_id,
            "lead_id": context["lead_id"],
            "deal_id": context.get("deal_id", ""),
            "amount": amount,
            "currency": context.get("currency", "USD"),
            "payment_method": context["payment_method"],
            "status": PaymentStatus.PROCESSING.value,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "description": context.get("description", "Product/Service Purchase"),
            "reference_number": context.get("reference_number", ""),
            "metadata": context.get("metadata", {}),
        }

        # Simulate payment processing
        if self._validate_payment(context):
            transaction["status"] = PaymentStatus.COMPLETED.value
            transaction["completed_at"] = datetime.now().isoformat()
            success = True
        else:
            transaction["status"] = PaymentStatus.FAILED.value
            success = False

        self.transactions[transaction_id] = transaction

        self.log_action("process_payment", {
            "transaction_id": transaction_id,
            "lead_id": context["lead_id"],
            "amount": amount,
            "status": transaction["status"],
        })

        return {
            "success": success,
            "transaction_id": transaction_id,
            "status": transaction["status"],
            "amount": amount,
            "transaction": transaction if success else None,
        }

    def authorize_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authorize a payment (pre-authorization without capturing).

        Args:
            context: Payment details for authorization

        Returns:
            Authorization result
        """
        required_fields = ["lead_id", "amount"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        auth_id = self._generate_auth_id()
        
        auth = {
            "authorization_id": auth_id,
            "lead_id": context["lead_id"],
            "amount": context["amount"],
            "status": "authorized",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().replace(day=datetime.now().day + 7)).isoformat(),
        }

        self.log_action("authorize_payment", {
            "auth_id": auth_id,
            "amount": context["amount"],
        })

        return {
            "success": True,
            "authorization_id": auth_id,
            "status": "authorized",
            "amount": context["amount"],
        }

    def capture_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture a previously authorized payment.

        Args:
            context: Contains authorization_id

        Returns:
            Capture result
        """
        required_fields = ["authorization_id"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        transaction_id = self._generate_transaction_id()
        
        transaction = {
            "transaction_id": transaction_id,
            "authorization_id": context["authorization_id"],
            "status": PaymentStatus.COMPLETED.value,
            "created_at": datetime.now().isoformat(),
        }

        self.transactions[transaction_id] = transaction

        self.log_action("capture_payment", {
            "transaction_id": transaction_id,
            "authorization_id": context["authorization_id"],
        })

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": PaymentStatus.COMPLETED.value,
        }

    def refund_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refund a completed payment.

        Args:
            context: Contains transaction_id and optional refund_amount

        Returns:
            Refund result
        """
        transaction_id = context.get("transaction_id")
        if transaction_id not in self.transactions:
            return {"success": False, "error": f"Transaction {transaction_id} not found"}

        original_transaction = self.transactions[transaction_id]
        
        if original_transaction["status"] != PaymentStatus.COMPLETED.value:
            return {"success": False, "error": "Can only refund completed transactions"}

        refund_amount = float(context.get("refund_amount", original_transaction["amount"]))
        
        if refund_amount > original_transaction["amount"]:
            return {"success": False, "error": "Refund amount exceeds transaction amount"}

        refund_id = self._generate_refund_id()
        
        refund = {
            "refund_id": refund_id,
            "transaction_id": transaction_id,
            "original_amount": original_transaction["amount"],
            "refund_amount": refund_amount,
            "status": PaymentStatus.REFUNDED.value,
            "created_at": datetime.now().isoformat(),
            "reason": context.get("reason", "Customer request"),
        }

        self.refunds[refund_id] = refund
        original_transaction["status"] = PaymentStatus.REFUNDED.value

        self.log_action("refund_payment", {
            "refund_id": refund_id,
            "transaction_id": transaction_id,
            "refund_amount": refund_amount,
        })

        return {
            "success": True,
            "refund_id": refund_id,
            "refund_amount": refund_amount,
            "status": PaymentStatus.REFUNDED.value,
        }

    def generate_invoice(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an invoice for a transaction.

        Args:
            context: Invoice details (transaction_id, customer_info, line_items)

        Returns:
            Generated invoice
        """
        transaction_id = context.get("transaction_id")
        if transaction_id and transaction_id not in self.transactions:
            return {"success": False, "error": f"Transaction {transaction_id} not found"}

        invoice_id = self._generate_invoice_id()
        
        invoice = {
            "invoice_id": invoice_id,
            "transaction_id": transaction_id,
            "lead_id": context.get("lead_id", ""),
            "customer_name": context.get("customer_name", ""),
            "customer_email": context.get("customer_email", ""),
            "customer_address": context.get("customer_address", ""),
            "issued_at": datetime.now().isoformat(),
            "due_date": context.get("due_date", ""),
            "line_items": context.get("line_items", []),
            "subtotal": 0,
            "tax": 0,
            "total": context.get("amount", 0),
            "notes": context.get("notes", ""),
            "status": "issued",
        }

        # Calculate totals from line items
        if invoice["line_items"]:
            invoice["subtotal"] = sum(item.get("amount", 0) for item in invoice["line_items"])
            invoice["tax"] = invoice["subtotal"] * 0.1  # 10% tax
            invoice["total"] = invoice["subtotal"] + invoice["tax"]

        self.invoices[invoice_id] = invoice

        self.log_action("generate_invoice", {
            "invoice_id": invoice_id,
            "transaction_id": transaction_id,
            "total": invoice["total"],
        })

        return {
            "success": True,
            "invoice_id": invoice_id,
            "invoice": invoice,
        }

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction details.

        Args:
            transaction_id: ID of transaction

        Returns:
            Transaction data
        """
        if transaction_id not in self.transactions:
            return {"success": False, "error": f"Transaction {transaction_id} not found"}

        return {
            "success": True,
            "transaction": self.transactions[transaction_id],
        }

    def get_payment_methods(self) -> Dict[str, Any]:
        """
        Get supported payment methods.

        Returns:
            List of available payment methods
        """
        methods = [
            {
                "name": method.value.replace("_", " ").title(),
                "value": method.value,
                "supported": True,
            }
            for method in PaymentMethod
        ]

        return {
            "success": True,
            "payment_methods": methods,
        }

    def _validate_payment(self, context: Dict[str, Any]) -> bool:
        """
        Validate payment details.

        Args:
            context: Payment context

        Returns:
            True if payment is valid
        """
        # Simulate validation
        # In production, this would validate with payment processor
        return True

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        tx_count = len(self.transactions) + 1
        return f"TXN_{timestamp}_{tx_count:06d}"

    def _generate_auth_id(self) -> str:
        """Generate a unique authorization ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"AUTH_{timestamp}_{len(self.transactions):05d}"

    def _generate_refund_id(self) -> str:
        """Generate a unique refund ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"REFUND_{timestamp}_{len(self.refunds) + 1:05d}"

    def _generate_invoice_id(self) -> str:
        """Generate a unique invoice ID."""
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"INV_{timestamp}_{len(self.invoices) + 1:04d}"
