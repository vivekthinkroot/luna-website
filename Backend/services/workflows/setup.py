"""
Workflow setup and initialization for Luna.

This module registers workflows and steps with the workflow system
using the centralized intent configuration.
"""

from utils.logger import get_logger

from ..intent_config import get_intent_registry
from .base import WorkflowDefinition
from .registry import get_workflow_registry
from .steps import (
    AddProfileStep,
    GenerateKundliStep,
    MainMenuStep,
    ProfileQnaStep,
    ProfileResolutionStep,
    UnknownFallbackStep,
)

logger = get_logger()


def initialize_workflows():
    """
    Initialize and register all workflows and steps.

    This function reads workflow configurations from the centralized intent registry
    and registers them with the workflow engine. This ensures consistency between
    intent definitions and workflow implementations.

    This function should be called at application startup to register
    all available workflows with the workflow engine.
    """
    registry = get_workflow_registry()
    intent_registry = get_intent_registry()

    # Register workflow steps
    registry.register_step(ProfileResolutionStep())
    registry.register_step(AddProfileStep())
    registry.register_step(GenerateKundliStep())
    registry.register_step(ProfileQnaStep())
    registry.register_step(UnknownFallbackStep())
    registry.register_step(MainMenuStep())

    # Register workflow definitions from intent configuration
    # All intents are now workflow-based
    all_intents = intent_registry.get_all_intents()

    for intent_id in all_intents:
        config = intent_registry.get_intent_config(intent_id)
        if config:
            # Create workflow definition from intent config
            # Use intent_id for both workflow_id and name (1:1 mapping)
            workflow = WorkflowDefinition(
                workflow_id=intent_id,
                name=intent_id.replace("_", " ").title(),
                description=config.description,
                steps=config.workflow_steps,
                initial_step=config.initial_step,
            )
            registry.register_workflow(workflow)
            logger.info(f"Registered workflow from intent config: {intent_id}")

    logger.info(
        f"Initialized {len(registry.list_workflows())} workflows and {len(registry.list_steps())} steps"
    )

    # Validate all workflows
    for workflow_id in registry.list_workflows():
        if registry.validate_workflow(workflow_id):
            logger.info(f"Validated workflow: {workflow_id}")
        else:
            logger.error(f"Failed to validate workflow: {workflow_id}")


def get_supported_workflow_intents():
    """
    Get list of intents that are supported by workflows.

    Returns:
        List of intent names that have workflow implementations
    """
    registry = get_workflow_registry()
    return registry.get_supported_intents()
