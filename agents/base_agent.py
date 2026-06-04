"""Base agent class for all sales agents."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class AgentStatus(Enum):
    """Agent operational states."""
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    PAUSED = "paused"


class BaseAgent(ABC):
    """Abstract base class for all sales agents."""

    def __init__(self, agent_id: str, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name of the agent
            config: Configuration dictionary for the agent
        """
        self.agent_id = agent_id
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.session_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Initialize logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the agent."""
        handler = logging.FileHandler(f"logs/{self.agent_id}.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.

        Args:
            context: Context data for execution

        Returns:
            Execution result
        """
        pass

    def start_session(self) -> None:
        """Start a new agent session."""
        self.status = AgentStatus.ACTIVE
        self.session_count += 1
        self.logger.info(f"Session {self.session_count} started")

    def end_session(self, success: bool = True) -> None:
        """
        End the current agent session.

        Args:
            success: Whether the session was successful
        """
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        self.status = AgentStatus.IDLE
        self.last_activity = datetime.now()
        self.logger.info(f"Session ended - Success: {success}")

    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """
        Log an agent action.

        Args:
            action: Description of the action
            details: Additional details about the action
        """
        self.last_activity = datetime.now()
        self.logger.info(f"{action}: {details}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.

        Returns:
            Status information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "sessions": self.session_count,
            "successes": self.success_count,
            "errors": self.error_count,
            "last_activity": self.last_activity.isoformat(),
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors that occur during execution.

        Args:
            error: The exception that occurred
            context: Context data when error occurred

        Returns:
            Error response
        """
        self.status = AgentStatus.ERROR
        self.error_count += 1
        self.logger.error(f"Error in {self.name}: {str(error)}", exc_info=True)
        
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now().isoformat(),
            "context": context,
        }

    def validate_context(
        self, 
        context: Dict[str, Any], 
        required_fields: List[str]
    ) -> bool:
        """
        Validate that context contains required fields.

        Args:
            context: Context to validate
            required_fields: List of required field names

        Returns:
            True if all required fields present
        """
        missing_fields = [f for f in required_fields if f not in context]
        
        if missing_fields:
            self.logger.warning(f"Missing required fields: {missing_fields}")
            return False
        
        return True
