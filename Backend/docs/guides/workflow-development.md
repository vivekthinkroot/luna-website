# Workflow Development Guide

## 🚀 Overview

Luna Server's workflow engine provides a powerful framework for creating complex, multi-step conversational flows with native LLM integration. This guide covers how to design, implement, and test custom workflows.

## 🏗️ Workflow Architecture

### **Core Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Engine                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              WorkflowEngine                                 │ │
│  │  • Orchestration • State Management • Step Execution       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Registry                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              WorkflowRegistry                               │ │
│  │  • Step Registration • Workflow Definitions • Validation   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Steps                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │  Step 1     │  │  Step 2     │  │  Step 3     │  │Step N│  │
│  │ (Native)    │  │ (Native)    │  │ (Native)    │  │(Native)│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Context Manager                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              WorkflowContextManager                         │ │
│  │  • State Persistence • Context Updates • Cleanup           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Concepts**

- **Workflow**: A sequence of steps that accomplish a specific user goal
- **Step**: Individual unit of work with LLM integration and state management
- **Context**: Structured state data that persists across workflow execution
- **Registry**: Central repository for workflows and steps
- **Engine**: Orchestrates workflow execution and state transitions

## 🔧 Creating a New Workflow

### **Step 1: Define Workflow State**

Create a Pydantic model for your workflow's state:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProfileCreationState(BaseModel):
    """State for profile creation workflow."""
    
    # User input fields
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Workflow control
    current_field: Optional[str] = None
    fields_completed: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_complete(self) -> bool:
        """Check if all required fields are completed."""
        required_fields = ["name", "birth_date", "birth_time", "birth_place"]
        return all(getattr(self, field) is not None for field in required_fields)
    
    @property
    def next_field(self) -> Optional[str]:
        """Get the next field that needs to be collected."""
        required_fields = ["name", "birth_date", "birth_time", "birth_place"]
        for field in required_fields:
            if getattr(self, field) is None:
                return field
        return None
```

### **Step 2: Implement Workflow Step**

Create your workflow step by extending the `WorkflowStep` base class:

```python
from services.workflows.base import WorkflowStep, StepResult, StepAction
from services.workflows.context import WorkflowContext
from llms.client import LLMClient
from typing import Dict, Any

class ProfileCreationStep(WorkflowStep):
    def __init__(self):
        super().__init__("profile_creation_native")
        self.workflow_id = "profile_creation"
        self.llm_client = LLMClient()
    
    async def execute(self, message: CanonicalRequestMessage, session: Session, 
                     workflow_context: WorkflowContext) -> StepResult:
        """Execute the profile creation workflow step."""
        
        # 1. Get current state
        state = ProfileCreationState(**workflow_context.get("profile_state", {}))
        
        # 2. Process user input
        if state.is_complete:
            return await self._handle_completion(message, session, state)
        else:
            return await self._handle_field_collection(message, session, state)
    
    async def _handle_field_collection(self, message: CanonicalRequestMessage, 
                                     session: Session, state: ProfileCreationState) -> StepResult:
        """Handle field collection phase."""
        
        # Use LLM to extract information from user message
        extraction_result = await self.llm_client.get_response(
            messages=self._build_extraction_messages(message, state),
            response_model=FieldExtractionResult,
            temperature=0.1
        )
        
        # Update state with extracted information
        if extraction_result.extracted_fields:
            for field, value in extraction_result.extracted_fields.items():
                setattr(state, field, value)
                if field not in state.fields_completed:
                    state.fields_completed.append(field)
        
        # Check if we're complete
        if state.is_complete:
            return await self._handle_completion(message, session, state)
        
        # Get next field to collect
        next_field = state.next_field
        prompt_message = self._build_field_prompt(next_field, state)
        
        # Create response asking for next field
        response = CanonicalResponseMessage(
            user_id=message.user_id,
            channel_type=message.channel_type,
            content=prompt_message,
            content_type=ContentType.TEXT,
            metadata={"workflow_id": self.workflow_id, "next_field": next_field}
        )
        
        # Update state
        state.last_updated = datetime.utcnow()
        
        return StepResult(
            response=response,
            action=StepAction.CONTINUE,
            context_updates={"profile_state": state.model_dump()}
        )
    
    async def _handle_completion(self, message: CanonicalRequestMessage, 
                               session: Session, state: ProfileCreationState) -> StepResult:
        """Handle workflow completion."""
        
        # Validate final state
        validation_result = await self._validate_profile_data(state)
        if not validation_result.is_valid:
            return await self._handle_validation_errors(message, session, state, validation_result)
        
        # Create profile in database
        profile = await self._create_profile(session.user_id, state)
        
        # Generate completion message
        completion_message = f"""
        🎉 Profile created successfully!
        
        **Profile Details:**
        • Name: {state.name}
        • Birth Date: {state.birth_date}
        • Birth Time: {state.birth_time}
        • Birth Place: {state.birth_place}
        
        Your profile is now ready for astrological services!
        """
        
        response = CanonicalResponseMessage(
            user_id=message.user_id,
            channel_type=message.channel_type,
            content=completion_message.strip(),
            content_type=ContentType.TEXT,
            metadata={
                "workflow_id": self.workflow_id,
                "profile_id": str(profile.profile_id),
                "status": "completed"
            }
        )
        
        # Mark workflow as complete
        state.last_updated = datetime.utcnow()
        
        return StepResult(
            response=response,
            action=StepAction.COMPLETE,
            context_updates={"profile_state": state.model_dump()}
        )
    
    def _build_extraction_messages(self, message: CanonicalRequestMessage, 
                                 state: ProfileCreationState) -> List[Dict[str, str]]:
        """Build messages for LLM field extraction."""
        
        system_prompt = f"""
        You are an astrological profile assistant. Extract relevant information from the user's message.
        
        Current profile state:
        - Name: {state.name or 'Not provided'}
        - Birth Date: {state.birth_date or 'Not provided'}
        - Birth Time: {state.birth_time or 'Not provided'}
        - Birth Place: {state.birth_place or 'Not provided'}
        
        Extract any of these fields from the user's message. If a field is already provided, don't change it.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message.content}
        ]
    
    def _build_field_prompt(self, field: str, state: ProfileCreationState) -> str:
        """Build prompt for requesting the next field."""
        
        field_prompts = {
            "name": "What is your full name?",
            "birth_date": "What is your birth date? (Please provide in DD/MM/YYYY format)",
            "birth_time": "What time were you born? (Please provide in HH:MM format, 24-hour)",
            "birth_place": "Where were you born? (City, Country)"
        }
        
        return field_prompts.get(field, f"Please provide your {field.replace('_', ' ')}.")
    
    async def _validate_profile_data(self, state: ProfileCreationState) -> ValidationResult:
        """Validate the collected profile data."""
        
        validation_result = ValidationResult()
        
        # Validate name
        if not state.name or len(state.name.strip()) < 2:
            validation_result.add_error("name", "Name must be at least 2 characters long")
        
        # Validate birth date
        try:
            datetime.strptime(state.birth_date, "%d/%m/%Y")
        except (ValueError, TypeError):
            validation_result.add_error("birth_date", "Birth date must be in DD/MM/YYYY format")
        
        # Validate birth time
        try:
            datetime.strptime(state.birth_time, "%H:%M")
        except (ValueError, TypeError):
            validation_result.add_error("birth_time", "Birth time must be in HH:MM format")
        
        # Validate coordinates
        if state.latitude is None or state.longitude is None:
            validation_result.add_error("birth_place", "Could not resolve location coordinates")
        
        return validation_result
    
    async def _create_profile(self, user_id: str, state: ProfileCreationState) -> TProfile:
        """Create profile in the database."""
        
        profile_data = {
            "user_id": int(user_id),
            "name": state.name,
            "birth_date": datetime.strptime(state.birth_date, "%d/%m/%Y").date(),
            "birth_time": datetime.strptime(state.birth_time, "%H:%M").time(),
            "birth_place": state.birth_place,
            "birth_latitude": state.latitude,
            "birth_longitude": state.longitude,
            "created_at": datetime.utcnow()
        }
        
        return self.profile_dao.create_profile(profile_data)
```

### **Step 3: Define Response Models**

Create Pydantic models for LLM responses:

```python
class FieldExtractionResult(BaseModel):
    """Result of field extraction from user message."""
    extracted_fields: Dict[str, Any] = {}
    confidence: float = 0.0
    reasoning: Optional[str] = None

class ValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool = True
    errors: Dict[str, str] = Field(default_factory=dict)
    
    def add_error(self, field: str, message: str):
        """Add a validation error."""
        self.errors[field] = message
        self.is_valid = False
```

### **Step 4: Register Your Workflow**

Add your workflow to the system in `services/workflows/setup.py`:

```python
def initialize_workflows():
    registry = get_workflow_registry()
    
    # Register your step
    registry.register_step(ProfileCreationStep())
    
    # Register workflow definition
    profile_creation_workflow = WorkflowDefinition(
        workflow_id="profile_creation",
        name="Profile Creation",
        description="Create a new astrological profile",
        steps=["profile_creation_native"],
        initial_step="profile_creation_native"
    )
    registry.register_workflow(profile_creation_workflow)
```

## 🔄 Workflow Execution Flow

### **Step Execution Lifecycle**

```
1. Workflow Engine receives execution request
    ↓
2. Retrieves or creates workflow context
    ↓
3. Determines current step
    ↓
4. Executes current step
    ↓
5. Processes step result
    ↓
6. Updates workflow context
    ↓
7. Determines next action
    ↓
8. Continues, completes, or waits
```

### **Step Result Actions**

```python
class StepAction(str, Enum):
    CONTINUE = "continue"      # Move to next step
    REPEAT = "repeat"          # Stay on current step
    JUMP = "jump"              # Jump to specific step
    WAIT = "wait"              # Wait for external event
    COMPLETE = "complete"      # Workflow finished
```

**Example Usage:**
```python
# Continue to next step
return StepResult(
    response=response,
    action=StepAction.CONTINUE,
    context_updates={"state": updated_state}
)

# Complete workflow
return StepResult(
    response=response,
    action=StepAction.COMPLETE,
    context_updates={"final_state": final_state}
)

# Wait for external event (e.g., payment confirmation)
return StepResult(
    response=response,
    action=StepAction.WAIT,
    context_updates={"waiting_for": "payment_confirmation"}
)
```

## 🎯 Advanced Workflow Patterns

### **Multi-Step Workflows**

Create workflows with multiple steps:

```python
class MultiStepProfileWorkflow(WorkflowStep):
    def __init__(self):
        super().__init__("multi_step_profile")
        self.workflow_id = "multi_step_profile"
        self.steps = ["basic_info", "location_resolution", "validation", "creation"]
    
    async def execute(self, message: CanonicalRequestMessage, session: Session, 
                     workflow_context: WorkflowContext) -> StepResult:
        """Execute multi-step profile creation."""
        
        current_step = workflow_context.get("current_step", "basic_info")
        
        if current_step == "basic_info":
            return await self._handle_basic_info(message, session, workflow_context)
        elif current_step == "location_resolution":
            return await self._handle_location_resolution(message, session, workflow_context)
        elif current_step == "validation":
            return await self._handle_validation(message, session, workflow_context)
        elif current_step == "creation":
            return await self._handle_creation(message, session, workflow_context)
        else:
            return await self._handle_error(message, session, workflow_context)
    
    async def _handle_basic_info(self, message: CanonicalRequestMessage, session: Session, 
                               workflow_context: WorkflowContext) -> StepResult:
        """Handle basic information collection."""
        
        # Collect basic info
        # ...
        
        # Move to next step
        return StepResult(
            response=response,
            action=StepAction.CONTINUE,
            context_updates={
                "current_step": "location_resolution",
                "basic_info": basic_info
            }
        )
```

### **Conditional Workflow Logic**

Implement conditional branching based on user responses:

```python
async def _handle_user_response(self, message: CanonicalRequestMessage, session: Session, 
                              workflow_context: WorkflowContext) -> StepResult:
    """Handle user response with conditional logic."""
    
    # Classify user response using LLM
    classification = await self.llm_client.get_response(
        messages=self._build_classification_messages(message),
        response_model=ResponseClassification,
        temperature=0.1
    )
    
    if classification.response_type == "confirmation":
        return await self._handle_confirmation(message, session, workflow_context)
    elif classification.response_type == "correction":
        return await self._handle_correction(message, session, workflow_context)
    elif classification.response_type == "question":
        return await self._handle_question(message, session, workflow_context)
    else:
        return await self._handle_unknown_response(message, session, workflow_context)
```

### **External Event Handling**

Handle external events like payment confirmations:

```python
async def handle_external_event(self, event_type: str, event_data: Dict[str, Any], 
                              workflow_context: WorkflowContext) -> StepResult:
    """Handle external events (e.g., payment confirmation)."""
    
    if event_type == "payment_confirmed":
        return await self._handle_payment_confirmation(event_data, workflow_context)
    elif event_type == "location_resolved":
        return await self._handle_location_resolution(event_data, workflow_context)
    else:
        logger.warning(f"Unknown event type: {event_type}")
        return None
```

## 🧪 Testing Your Workflows

### **Unit Testing**

Test individual workflow steps:

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestProfileCreationStep:
    @pytest.fixture
    def step(self):
        return ProfileCreationStep()
    
    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session.user_id = "test_user"
        return session
    
    @pytest.fixture
    def mock_workflow_context(self):
        return {
            "profile_state": {
                "name": None,
                "birth_date": None,
                "birth_time": None,
                "birth_place": None
            }
        }
    
    @pytest.mark.asyncio
    async def test_field_collection(self, step, mock_session, mock_workflow_context):
        """Test field collection phase."""
        
        message = CanonicalRequestMessage(
            user_id="test_user",
            channel_type=ChannelType.TELEGRAM,
            channel_user_id="123",
            content="My name is John Doe",
            content_type=ContentType.TEXT
        )
        
        # Mock LLM response
        step.llm_client.get_response = AsyncMock(return_value=Mock(
            extracted_fields={"name": "John Doe"}
        ))
        
        result = await step.execute(message, mock_session, mock_workflow_context)
        
        assert result.action == StepAction.CONTINUE
        assert "name" in result.context_updates["profile_state"]["fields_completed"]
    
    @pytest.mark.asyncio
    async def test_workflow_completion(self, step, mock_session, mock_workflow_context):
        """Test workflow completion."""
        
        # Set up complete state
        mock_workflow_context["profile_state"] = {
            "name": "John Doe",
            "birth_date": "15/01/1990",
            "birth_time": "14:30",
            "birth_place": "New York, USA",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        message = CanonicalRequestMessage(
            user_id="test_user",
            channel_type=ChannelType.TELEGRAM,
            channel_user_id="123",
            content="That's correct",
            content_type=ContentType.TEXT
        )
        
        # Mock profile creation
        step.profile_dao.create_profile = Mock(return_value=Mock(profile_id=1))
        
        result = await step.execute(message, mock_session, mock_workflow_context)
        
        assert result.action == StepAction.COMPLETE
        assert "profile_id" in result.response.metadata
```

### **Integration Testing**

Test complete workflow execution:

```python
@pytest.mark.asyncio
async def test_profile_creation_workflow_integration():
    """Test complete profile creation workflow."""
    
    # Initialize workflow engine
    workflow_engine = WorkflowEngine()
    
    # Create test message
    message = CanonicalRequestMessage(
        user_id="test_user",
        channel_type=ChannelType.TELEGRAM,
        channel_user_id="123",
        content="I want to create a profile",
        content_type=ContentType.TEXT
    )
    
    # Create test session
    session = Session(user_id="test_user")
    
    # Execute workflow
    response = await workflow_engine.execute_workflow(
        "profile_creation", message, session
    )
    
    # Verify response
    assert response is not None
    assert "name" in response.content.lower()
    
    # Verify workflow context was created
    context = workflow_engine.context_manager.get_context("test_user", "profile_creation")
    assert context is not None
    assert context.get("current_step") == "profile_creation_native"
```

## 🚀 Best Practices

### **State Management**

1. **Use Pydantic Models**: Ensure type safety and validation
2. **Immutable Updates**: Create new state objects rather than modifying existing ones
3. **Clear State Structure**: Organize state data logically
4. **State Validation**: Validate state at each step

### **LLM Integration**

1. **Structured Prompts**: Use clear, structured prompts for consistent responses
2. **Response Models**: Define Pydantic models for LLM responses
3. **Error Handling**: Handle LLM failures gracefully
4. **Temperature Control**: Use appropriate temperature settings for different tasks

### **Error Handling**

1. **Graceful Degradation**: Provide fallbacks when things go wrong
2. **User Guidance**: Give users clear instructions on how to proceed
3. **Logging**: Log errors for debugging and monitoring
4. **Recovery**: Allow users to recover from errors

### **Performance Optimization**

1. **Async Operations**: Use async/await for I/O operations
2. **State Caching**: Cache frequently accessed state data
3. **LLM Optimization**: Minimize LLM calls and optimize prompts
4. **Resource Management**: Clean up resources properly


---

This workflow development guide provides a comprehensive foundation for creating sophisticated conversational workflows in Luna Server. By following these patterns and best practices, you can build robust, maintainable workflows that provide excellent user experiences.
