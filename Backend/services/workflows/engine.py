"""
Workflow execution engine for Luna.

This module provides the core workflow execution logic that orchestrates
complex multi-step conversational flows.
"""

from typing import Any, Dict, Optional

from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage
from utils.sessions import Session

from .base import StepAction, StepResult
from .context import WorkflowContext, WorkflowContextManager
from .registry import get_workflow_registry

"""
if TYPE_CHECKING:
    from utils.models import (
        CanonicalRequestMessage,
        CanonicalResponseMessage,
        ContentType,
    )
"""

logger = get_logger()


class WorkflowEngine:
    """
    Core workflow execution engine.

    Manages workflow lifecycle, step execution, and state transitions.
    Provides the main interface for executing workflows in response to
    user messages and external events.
    """

    def __init__(self):
        self.registry = get_workflow_registry()

    async def execute_workflow(
        self, workflow_id: str, message: CanonicalRequestMessage, session: Session
    ) -> CanonicalResponseMessage:
        """
        Execute a workflow for the given intent and message.

        Args:
            workflow_id: ID of the workflow to execute (usually matches intent)
            message: User message that triggered the workflow
            session: User session data

        Returns:
            Response message from the workflow execution
        """
        try:
            # Get workflow definition
            workflow_def = self.registry.get_workflow(workflow_id)
            if not workflow_def:
                logger.error(f"Workflow not found: {workflow_id}")
                return self._create_error_response(
                    message, f"Workflow {workflow_id} not configured"
                )

            # Validate workflow
            if not self.registry.validate_workflow(workflow_id):
                logger.error(f"Invalid workflow configuration: {workflow_id}")
                return self._create_error_response(
                    message, "Workflow configuration error"
                )

            # Get or create workflow context
            context = WorkflowContextManager.get_workflow_context(session, workflow_id)
            if not context:
                # Start new workflow
                context = WorkflowContextManager.create_workflow_context(
                    session=session,
                    workflow_id=workflow_id,
                    initial_step_id=workflow_def.initial_step,
                )
                # Set the active intent to the new workflow
                session.set_active_intent(workflow_id)
                logger.info(
                    f"Started new workflow {workflow_id} for user {session.user_id}"
                )

            # Check if workflow is waiting for an event
            if context.is_waiting:
                logger.info(
                    f"Workflow {workflow_id} is waiting for event, ignoring user message"
                )
                return self._create_waiting_response(message, context)

            # Execute current step
            return await self._execute_step(
                workflow_def=workflow_def,
                context=context,
                message=message,
                session=session,
            )

        except Exception as e:
            logger.exception(f"Error executing workflow {workflow_id}: {e}")
            return self._create_error_response(
                message, "An error occurred processing your request"
            )

    async def handle_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        session: Session,
    ) -> Optional[CanonicalResponseMessage]:
        """
        Handle external events for waiting workflows.

        Args:
            user_id: ID of the user
            event_type: Type of event (e.g., "payment_success")
            event_data: Event payload
            session: User session data

        Returns:
            Response message if workflow was resumed, None if no workflow was waiting
        """
        try:
            # Find workflows waiting for this event type
            if "workflows" not in session.session_metadata:
                return None

            for workflow_id, workflow_data in session.session_metadata[
                "workflows"
            ].items():
                context = WorkflowContextManager.get_workflow_context(
                    session, workflow_id
                )
                if not context or not context.is_waiting:
                    continue

                if (
                    context.wait_event
                    and context.wait_event.get("event_type") == event_type
                ):

                    logger.info(
                        f"Resuming workflow {workflow_id} for event {event_type}"
                    )

                    # Get current step and handle event
                    step = self.registry.get_step(context.current_step_id)
                    if not step:
                        logger.error(f"Step not found: {context.current_step_id}")
                        continue

                    # Let step handle the event
                    result = await step.on_event(
                        event_type=event_type,
                        event_data=event_data,
                        workflow_id=workflow_id,
                        workflow_context=context.context_data,
                    )

                    if result:
                        # Update context and continue workflow
                        WorkflowContextManager.update_workflow_context(
                            session=session, context=context, is_waiting=False
                        )

                        return await self._handle_step_result(
                            workflow_def=self.registry.get_workflow(workflow_id),
                            context=context,
                            result=result,
                            session=session,
                        )

            return None

        except Exception as e:
            logger.exception(f"Error handling event {event_type}: {e}")
            return None

    async def _execute_step(
        self,
        workflow_def,
        context: WorkflowContext,
        message: CanonicalRequestMessage,
        session: Session,
    ) -> CanonicalResponseMessage:
        """Execute the current step in the workflow."""

        # Get step instance
        step = self.registry.get_step(context.current_step_id)
        if not step:
            logger.error(f"Step not found: {context.current_step_id}")
            return self._create_error_response(message, "Workflow step not found")

        # Execute step
        logger.info(
            f"Executing step {context.current_step_id} in workflow {context.workflow_id}"
        )
        result = await step.execute(
            message=message,
            session=session,
            workflow_id=context.workflow_id,
            workflow_context=context.context_data,
        )

        return await self._handle_step_result(
            workflow_def=workflow_def,
            context=context,
            result=result,
            session=session,
            message=message,
        )

    async def _handle_step_result(
        self,
        workflow_def,
        context: WorkflowContext,
        result: StepResult,
        session: Session,
        message: CanonicalRequestMessage,
    ) -> CanonicalResponseMessage:
        """Handle the result of step execution."""

        # Update context data if provided
        if result.context_updates:
            WorkflowContextManager.update_workflow_context(
                session=session, context=context, context_updates=result.context_updates
            )

        # Handle action
        if result.action == StepAction.CONTINUE:
            # Move to next step
            # Prioritize next_step_id from result context if available, otherwise use workflow definition
            next_step = result.next_step_id or workflow_def.get_next_step(
                context.current_step_id
            )
            if next_step:
                WorkflowContextManager.update_workflow_context(
                    session=session,
                    context=context,
                    step_id=next_step,
                )
                logger.info(
                    f"Advanced to step {next_step} in workflow {context.workflow_id}"
                )
            else:
                # End of workflow
                logger.info(f"Completed workflow {context.workflow_id}")
                WorkflowContextManager.clear_workflow_context(
                    session, context.workflow_id
                )
        elif result.action == StepAction.ADVANCE_NOW:
            # Move to next step AND immediately execute it in this turn
            # Prioritize next_step_id from result context if available, otherwise use workflow definition
            next_step = result.next_step_id or workflow_def.get_next_step(
                context.current_step_id
            )
            if next_step:
                WorkflowContextManager.update_workflow_context(
                    session=session,
                    context=context,
                    step_id=next_step,
                )
                logger.info(
                    f"Immediately advancing to step {next_step} in workflow {context.workflow_id}"
                )
                # Execute the next step now with the same message
                return await self._execute_step(
                    workflow_def=workflow_def,
                    context=context,
                    message=message,
                    session=session,
                )
            else:
                logger.info(f"Completed workflow {context.workflow_id}")
                WorkflowContextManager.clear_workflow_context(
                    session, context.workflow_id
                )

        elif result.action == StepAction.REPEAT:
            # Stay on current step - no context update needed
            logger.info(
                f"Repeating step {context.current_step_id} in workflow {context.workflow_id}"
            )

        elif result.action == StepAction.JUMP:
            # Jump to specified step or workflow
            if result.next_workflow_id:
                # Transition to a different workflow
                logger.info(
                    f"Transitioning from workflow {context.workflow_id} to {result.next_workflow_id}"
                )
                # Clear current workflow context
                WorkflowContextManager.clear_workflow_context(
                    session, context.workflow_id
                )

                # Start new workflow
                new_workflow_def = self.registry.get_workflow(result.next_workflow_id)
                if not new_workflow_def:
                    logger.error(
                        f"Target workflow not found: {result.next_workflow_id}"
                    )
                    # For workflow transitions, we can't create error responses
                    # Just log the error and return the current response
                    return result.response

                # Create new workflow context
                # Carry over any existing handoff data to the new workflow
                existing_handoff = (
                    context.context_data.get("_handoff")
                    if context and context.context_data
                    else None
                )
                new_context = WorkflowContextManager.create_workflow_context(
                    session=session,
                    workflow_id=result.next_workflow_id,
                    initial_step_id=result.next_step_id
                    or new_workflow_def.initial_step,
                    initial_data=(
                        {"_handoff": existing_handoff} if existing_handoff else None
                    ),
                )
                logger.info(
                    f"Set up new workflow {result.next_workflow_id} for user {session.user_id}"
                )

                # Set the active intent to the new workflow
                session.set_active_intent(result.next_workflow_id)

                # Don't execute the first step immediately - let it happen on next user message
                # This makes the engine truly message-agnostic
                return result.response

            elif result.next_step_id:
                # Jump within current workflow
                WorkflowContextManager.update_workflow_context(
                    session=session, context=context, step_id=result.next_step_id
                )
                logger.info(
                    f"Jumped to step {result.next_step_id} in workflow {context.workflow_id}"
                )

        elif result.action == StepAction.WAIT:
            # Wait for external event
            WorkflowContextManager.update_workflow_context(
                session=session,
                context=context,
                is_waiting=True,
                wait_event=result.wait_for,
            )
            logger.info(
                f"Workflow {context.workflow_id} waiting for event: {result.wait_for}"
            )

        elif result.action == StepAction.COMPLETE:
            # Complete workflow
            logger.info(f"Completed workflow {context.workflow_id}")
            # Clear active intent to avoid biasing follow-up classification
            session.set_active_intent(None)
            WorkflowContextManager.clear_workflow_context(session, context.workflow_id)

        return result.response

    def _create_error_response(
        self, message: CanonicalRequestMessage, error_msg: str
    ) -> CanonicalResponseMessage:
        """Create a standard error response."""
        return message.create_error_response(
            error_message="I'm sorry, something went wrong. Please try again.",
            metadata={"error": error_msg},
        )

    def _create_waiting_response(
        self, message: CanonicalRequestMessage, context: WorkflowContext
    ) -> CanonicalResponseMessage:
        """Create a response when workflow is waiting for an event."""
        wait_msg = "I'm still processing your previous request. Please wait a moment."

        if context.wait_event:
            event_type = context.wait_event.get("event_type", "")
            if "payment" in event_type.lower():
                wait_msg = "I'm waiting for your payment to be processed. Please complete the payment and I'll continue with your request."

        return message.create_text_response(
            content=wait_msg,
            metadata={"workflow_waiting": True},
        )
