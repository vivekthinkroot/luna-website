"""
Workflow context management for Luna workflows.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel

from utils.sessions import Session


class WorkflowContext(BaseModel):
    """
    Manages workflow-specific state and data.

    This class handles persistence of workflow state in the user session
    and provides a clean interface for steps to access and update context.
    """

    workflow_id: str
    current_step_id: str
    context_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    is_waiting: bool = False
    wait_event: Optional[Dict[str, Any]] = None

    class Config:
        # Allow datetime objects to be serialized
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowContextManager:
    """Manages workflow context storage in user sessions."""

    WORKFLOW_KEY = "workflows"

    @classmethod
    def get_workflow_context(
        cls, session: Session, workflow_id: str
    ) -> Optional[WorkflowContext]:
        """
        Retrieve workflow context from session.

        Args:
            session: User session
            workflow_id: ID of the workflow

        Returns:
            WorkflowContext if found, None otherwise
        """
        if cls.WORKFLOW_KEY not in session.session_metadata:
            return None

        workflow_data = session.session_metadata[cls.WORKFLOW_KEY].get(workflow_id)
        if not workflow_data:
            return None

        try:
            # Convert datetime strings back to datetime objects
            if isinstance(workflow_data.get("created_at"), str):
                workflow_data["created_at"] = datetime.fromisoformat(
                    workflow_data["created_at"]
                )
            if isinstance(workflow_data.get("updated_at"), str):
                workflow_data["updated_at"] = datetime.fromisoformat(
                    workflow_data["updated_at"]
                )

            return WorkflowContext(**workflow_data)
        except Exception:
            # If context is corrupted, return None to trigger fresh start
            return None

    @classmethod
    def save_workflow_context(cls, session: Session, context: WorkflowContext) -> None:
        """
        Save workflow context to session.

        Args:
            session: User session
            context: Workflow context to save
        """
        if cls.WORKFLOW_KEY not in session.session_metadata:
            session.session_metadata[cls.WORKFLOW_KEY] = {}

        # Update timestamp
        context.updated_at = datetime.now(timezone.utc)

        # Save to session
        session.session_metadata[cls.WORKFLOW_KEY][
            context.workflow_id
        ] = context.model_dump()

    @classmethod
    def create_workflow_context(
        cls,
        session: Session,
        workflow_id: str,
        initial_step_id: str,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowContext:
        """
        Create a new workflow context.

        Args:
            session: User session
            workflow_id: ID of the workflow
            initial_step_id: ID of the first step
            initial_data: Initial context data

        Returns:
            New WorkflowContext
        """
        now = datetime.now(timezone.utc)

        context = WorkflowContext(
            workflow_id=workflow_id,
            current_step_id=initial_step_id,
            context_data=initial_data or {},
            created_at=now,
            updated_at=now,
        )

        cls.save_workflow_context(session, context)
        return context

    @classmethod
    def update_workflow_context(
        cls,
        session: Session,
        context: WorkflowContext,
        step_id: Optional[str] = None,
        context_updates: Optional[Dict[str, Any]] = None,
        is_waiting: Optional[bool] = None,
        wait_event: Optional[Dict[str, Any]] = None,
    ) -> WorkflowContext:
        """
        Update workflow context with new values.

        Args:
            session: User session
            context: Current context
            step_id: New step ID if changing steps
            context_updates: Updates to context data
            is_waiting: Whether workflow is waiting for external event
            wait_event: Event details if waiting

        Returns:
            Updated WorkflowContext
        """
        if step_id is not None:
            context.current_step_id = step_id

        if context_updates:
            context.context_data.update(context_updates)

        if is_waiting is not None:
            context.is_waiting = is_waiting

        if wait_event is not None:
            context.wait_event = wait_event
        elif is_waiting is False:
            # Clear wait event when no longer waiting
            context.wait_event = None

        cls.save_workflow_context(session, context)
        return context

    @classmethod
    def clear_workflow_context(cls, session: Session, workflow_id: str) -> None:
        """
        Clear workflow context from session.

        Args:
            session: User session
            workflow_id: ID of workflow to clear
        """
        if cls.WORKFLOW_KEY in session.session_metadata:
            session.session_metadata[cls.WORKFLOW_KEY].pop(workflow_id, None)

            # Clean up empty workflows dict
            if not session.session_metadata[cls.WORKFLOW_KEY]:
                del session.session_metadata[cls.WORKFLOW_KEY]
