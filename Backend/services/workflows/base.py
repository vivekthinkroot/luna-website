"""
Base classes for the workflow system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import BaseModel

from utils.models import CanonicalRequestMessage, CanonicalResponseMessage
from utils.sessions import Session

if TYPE_CHECKING:
    from utils.models import CanonicalRequestMessage, CanonicalResponseMessage


class StepAction(str, Enum):
    """Possible actions a workflow step can return."""

    CONTINUE = "continue"  # Move to next step
    REPEAT = "repeat"  # Stay on current step (for multi-turn conversations)
    JUMP = "jump"  # Jump to specific step
    WAIT = "wait"  # Wait for external event
    COMPLETE = "complete"  # Complete workflow
    ADVANCE_NOW = "advance_now"  # Immediately execute the next step in this turn


class StepResult(BaseModel):
    """Result returned by a workflow step execution."""

    response: CanonicalResponseMessage
    action: StepAction
    next_step_id: Optional[str] = None
    next_workflow_id: Optional[str] = None  # Transition to different workflow
    wait_for: Optional[Dict[str, Any]] = None  # Event details for WAIT action
    context_updates: Optional[Dict[str, Any]] = None  # Updates to workflow context


class WorkflowStep(ABC):
    """
    Abstract base class for all workflow steps.

    Each step represents a single logical unit of work in a conversational flow.
    Steps can be LLM-driven (for natural conversation) or service-driven
    (for API calls, data processing, etc.).
    """

    def __init__(self, step_id: str):
        self.step_id = step_id

    @abstractmethod
    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """
        Execute this step with the given context.

        Args:
            message: The user's message that triggered this step
            session: User session data
            workflow_context: Workflow-specific context data

        Returns:
            StepResult: The result of step execution
        """
        pass

    async def on_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> Optional[StepResult]:
        """
        Handle external events (payment callbacks, async job completion, etc.).

        Args:
            event_type: Type of event (e.g., "payment_success")
            event_data: Event payload
            workflow_context: Current workflow context

        Returns:
            Optional StepResult: None if event not handled, result if handled
        """
        return None

    def get_step_id(self) -> str:
        """Get the unique identifier for this step."""
        return self.step_id


class WorkflowDefinition(BaseModel):
    """Definition of a complete workflow."""

    workflow_id: str
    name: str
    description: str
    steps: list[str]  # Ordered list of step IDs
    initial_step: str

    def get_next_step(self, current_step: str) -> Optional[str]:
        """Get the next step in the linear sequence."""
        try:
            current_index = self.steps.index(current_step)
            if current_index + 1 < len(self.steps):
                return self.steps[current_index + 1]
        except ValueError:
            pass
        return None
