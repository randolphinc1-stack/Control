"""Agent for managing phone calls and voice interactions."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
from .base_agent import BaseAgent


class CallType(Enum):
    """Type of phone call."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(Enum):
    """Call status."""
    QUEUED = "queued"
    RINGING = "ringing"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    FAILED = "failed"
    DECLINED = "declined"


class CallOutcome(Enum):
    """Outcome of a call."""
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    DISCONNECTED = "disconnected"
    TRANSFERRED = "transferred"


class PhoneCallAgent(BaseAgent):
    """Agent for managing phone calls and voice interactions."""

    def __init__(self, agent_id: str = "call_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the phone call agent."""
        super().__init__(agent_id, "Phone Call Agent", config)
        self.calls: Dict[str, Dict[str, Any]] = {}
        self.call_queue: List[Dict[str, Any]] = []
        self.active_calls: Dict[str, Dict[str, Any]] = {}

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute phone call logic.

        Args:
            context: Contains action and call parameters

        Returns:
            Operation result
        """
        try:
            self.start_session()
            
            action = context.get("action", "handle_inbound_call")
            
            if action == "handle_inbound_call":
                result = self.handle_inbound_call(context)
            elif action == "initiate_outbound_call":
                result = self.initiate_outbound_call(context)
            elif action == "answer_call":
                result = self.answer_call(context.get("call_id"))
            elif action == "end_call":
                result = self.end_call(context.get("call_id"), context)
            elif action == "transfer_call":
                result = self.transfer_call(context.get("call_id"), context)
            elif action == "get_call_status":
                result = self.get_call_status(context.get("call_id"))
            elif action == "get_call_history":
                result = self.get_call_history(context.get("lead_id"))
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.end_session(success=True)
            return result
            
        except Exception as e:
            return self.handle_error(e, context)

    def handle_inbound_call(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an inbound call.

        Args:
            context: Call information (from_number, lead_id)

        Returns:
            Call handler result
        """
        required_fields = ["from_number"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        call_id = self._generate_call_id()
        
        call = {
            "call_id": call_id,
            "call_type": CallType.INBOUND.value,
            "from_number": context["from_number"],
            "to_number": context.get("to_number", "main_line"),
            "lead_id": context.get("lead_id", ""),
            "status": CallStatus.RINGING.value,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "duration_seconds": 0,
            "outcome": None,
            "recording_url": None,
            "transcript": None,
            "notes": context.get("notes", ""),
            "agent_notes": "",
            "transfer_target": None,
        }

        self.calls[call_id] = call
        self.call_queue.append(call)

        self.log_action("handle_inbound_call", {
            "call_id": call_id,
            "from_number": context["from_number"],
        })

        return {
            "success": True,
            "call_id": call_id,
            "action": "answer_or_queue",
            "queue_position": len(self.call_queue),
        }

    def initiate_outbound_call(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate an outbound call.

        Args:
            context: Call information (to_number, lead_id, script)

        Returns:
            Call initiation result
        """
        required_fields = ["to_number"]
        if not self.validate_context(context, required_fields):
            return {"success": False, "error": "Missing required fields"}

        call_id = self._generate_call_id()
        
        call = {
            "call_id": call_id,
            "call_type": CallType.OUTBOUND.value,
            "from_number": context.get("from_number", "main_line"),
            "to_number": context["to_number"],
            "lead_id": context.get("lead_id", ""),
            "status": CallStatus.QUEUED.value,
            "started_at": None,
            "ended_at": None,
            "duration_seconds": 0,
            "outcome": None,
            "recording_url": None,
            "transcript": None,
            "script": context.get("script", ""),
            "notes": context.get("notes", ""),
            "agent_notes": "",
            "transfer_target": None,
        }

        self.calls[call_id] = call
        self.call_queue.append(call)

        self.log_action("initiate_outbound_call", {
            "call_id": call_id,
            "to_number": context["to_number"],
            "lead_id": context.get("lead_id", ""),
        })

        return {
            "success": True,
            "call_id": call_id,
            "status": CallStatus.QUEUED.value,
            "message": "Call queued for dialing",
        }

    def answer_call(self, call_id: str) -> Dict[str, Any]:
        """
        Answer a queued or ringing call.

        Args:
            call_id: ID of call to answer

        Returns:
            Call answer result
        """
        if call_id not in self.calls:
            return {"success": False, "error": f"Call {call_id} not found"}

        call = self.calls[call_id]
        call["status"] = CallStatus.ACTIVE.value
        call["started_at"] = datetime.now().isoformat()
        
        if call_id not in self.active_calls:
            self.active_calls[call_id] = call

        self.log_action("answer_call", {"call_id": call_id})

        return {
            "success": True,
            "call_id": call_id,
            "status": CallStatus.ACTIVE.value,
            "message": "Call answered",
            "caller_info": {
                "from_number": call["from_number"],
                "lead_id": call.get("lead_id", ""),
            },
        }

    def end_call(self, call_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        End an active call.

        Args:
            call_id: ID of call to end
            context: End call details (outcome, agent_notes, transcript)

        Returns:
            Call end result
        """
        if call_id not in self.calls:
            return {"success": False, "error": f"Call {call_id} not found"}

        call = self.calls[call_id]
        
        # Calculate call duration
        if call["started_at"]:
            start = datetime.fromisoformat(call["started_at"])
            duration = (datetime.now() - start).total_seconds()
            call["duration_seconds"] = int(duration)
        
        call["status"] = CallStatus.COMPLETED.value
        call["ended_at"] = datetime.now().isoformat()
        call["outcome"] = context.get("outcome", CallOutcome.SUCCESSFUL.value)
        call["agent_notes"] = context.get("agent_notes", "")
        call["transcript"] = context.get("transcript", "")
        call["recording_url"] = context.get("recording_url", "")
        
        if call_id in self.active_calls:
            del self.active_calls[call_id]

        self.log_action("end_call", {
            "call_id": call_id,
            "duration": call["duration_seconds"],
            "outcome": call["outcome"],
        })

        return {
            "success": True,
            "call_id": call_id,
            "duration_seconds": call["duration_seconds"],
            "outcome": call["outcome"],
        }

    def transfer_call(self, call_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transfer a call to another agent or number.

        Args:
            call_id: ID of call to transfer
            context: Transfer details (target_number or target_agent)

        Returns:
            Transfer result
        """
        if call_id not in self.calls:
            return {"success": False, "error": f"Call {call_id} not found"}

        target = context.get("target_number") or context.get("target_agent")
        if not target:
            return {"success": False, "error": "No transfer target specified"}

        call = self.calls[call_id]
        call["status"] = CallStatus.ON_HOLD.value
        call["transfer_target"] = target

        self.log_action("transfer_call", {
            "call_id": call_id,
            "transfer_target": target,
        })

        return {
            "success": True,
            "call_id": call_id,
            "transfer_target": target,
            "message": "Call transferred",
        }

    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Get the status of a call.

        Args:
            call_id: ID of call

        Returns:
            Call status
        """
        if call_id not in self.calls:
            return {"success": False, "error": f"Call {call_id} not found"}

        call = self.calls[call_id]
        return {
            "success": True,
            "call_id": call_id,
            "call": call,
        }

    def get_call_history(self, lead_id: str) -> Dict[str, Any]:
        """
        Get call history for a lead.

        Args:
            lead_id: ID of lead

        Returns:
            List of calls for the lead
        """
        calls = [c for c in self.calls.values() if c.get("lead_id") == lead_id]
        calls.sort(key=lambda c: c["started_at"] or "", reverse=True)

        return {
            "success": True,
            "lead_id": lead_id,
            "count": len(calls),
            "calls": calls,
        }

    def get_active_calls(self) -> Dict[str, Any]:
        """
        Get all currently active calls.

        Returns:
            List of active calls
        """
        return {
            "success": True,
            "count": len(self.active_calls),
            "calls": list(self.active_calls.values()),
        }

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the status of the call queue.

        Returns:
            Queue information
        """
        waiting_calls = [c for c in self.call_queue if c["status"] in [
            CallStatus.QUEUED.value,
            CallStatus.RINGING.value,
        ]]

        return {
            "success": True,
            "queue_length": len(waiting_calls),
            "active_calls": len(self.active_calls),
            "total_calls": len(self.calls),
            "queued_calls": waiting_calls,
        }

    def _generate_call_id(self) -> str:
        """Generate a unique call ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:14]
        call_count = len(self.calls) + 1
        return f"CALL_{timestamp}_{call_count:05d}"
