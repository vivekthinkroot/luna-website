"""
Workflow registry for Luna workflows.

This module manages workflow definitions and step registrations.
"""

from typing import Dict, List, Optional

from utils.logger import get_logger

from .base import WorkflowDefinition, WorkflowStep

logger = get_logger()


class WorkflowRegistry:
    """
    Central registry for workflows and steps.

    Manages workflow definitions and step instances, providing
    lookup capabilities for the workflow engine.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._steps: Dict[str, WorkflowStep] = {}

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        """
        Register a workflow definition.

        Args:
            definition: Workflow definition to register
        """
        self._workflows[definition.workflow_id] = definition
        logger.info(f"Registered workflow: {definition.workflow_id}")

    def register_step(self, step: WorkflowStep) -> None:
        """
        Register a workflow step.

        Args:
            step: Step instance to register
        """
        self._steps[step.get_step_id()] = step
        logger.info(f"Registered workflow step: {step.get_step_id()}")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get workflow definition by ID.

        Args:
            workflow_id: ID of workflow to retrieve

        Returns:
            WorkflowDefinition if found, None otherwise
        """
        return self._workflows.get(workflow_id)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """
        Get step instance by ID.

        Args:
            step_id: ID of step to retrieve

        Returns:
            WorkflowStep if found, None otherwise
        """
        return self._steps.get(step_id)

    def get_supported_intents(self) -> List[str]:
        """
        Get list of intents that have workflow support.

        Returns:
            List of supported intent names
        """
        return list(self._workflows.keys())

    def validate_workflow(self, workflow_id: str) -> bool:
        """
        Validate that a workflow has all required steps registered.

        Args:
            workflow_id: ID of workflow to validate

        Returns:
            True if workflow is valid, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        # Check that all steps are registered
        for step_id in workflow.steps:
            if step_id not in self._steps:
                logger.error(
                    f"Workflow {workflow_id} references unregistered step: {step_id}"
                )
                return False

        # Check that initial step is in the step list
        if workflow.initial_step not in workflow.steps:
            logger.error(
                f"Workflow {workflow_id} initial step {workflow.initial_step} not in steps list"
            )
            return False

        return True

    def list_workflows(self) -> List[str]:
        """
        List all registered workflow IDs.

        Returns:
            List of workflow IDs
        """
        return list(self._workflows.keys())

    def list_steps(self) -> List[str]:
        """
        List all registered step IDs.

        Returns:
            List of step IDs
        """
        return list(self._steps.keys())


# Global registry instance
workflow_registry = WorkflowRegistry()


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry instance."""
    return workflow_registry
