# Intent Management Guide

## 🎯 Understanding User Intents

User intents represent what users want to accomplish when they interact with Luna Server. The system uses Large Language Models (LLMs) to intelligently classify these intents and route users to appropriate workflows or handlers.

## 🏗️ Intent System Architecture

### **Centralized Intent Management**

Luna Server uses a centralized intent management system where all intent definitions, descriptions, and workflow configurations are managed in a single place:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Registry                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              services/intent_config.py                     │ │
│  │  • Intent Definitions • Descriptions • Workflow Mapping    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Router Service                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              services/router.py                             │ │
│  │  • LLM Classification • Intent Routing • Workflow Engine   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┐
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Engine                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              services/workflows/                            │ │
│  │  • Native Steps • State Management • Context Persistence   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Intent Classification Flow**

```
User Message
    ↓
Session Context Retrieval
    ↓
LLM-Based Classification
    ↓
Intent Validation
    ↓
Workflow/Handler Selection
    ↓
Execution
```

## 📋 Current Intent Categories

### **1. Profile Management Intents**

#### **`add_profile`**
- **Description**: User wants to create a new astrological profile
- **Workflow**: `AddProfileStep` (native LLM integration)
- **Features**: 
  - Structured field collection
  - Birth data validation
  - Location resolution
  - Profile persistence

**Example User Messages:**
- "I want to create a new profile"
- "Add my birth details"
- "Create profile for me"
- "I need to set up my astrological profile"

#### **`switch_profile`**
- **Description**: User wants to switch between multiple profiles
- **Workflow**: Profile selection workflow
- **Features**: Profile listing, selection, and activation

**Example User Messages:**
- "Switch to my other profile"
- "Change profile"
- "Use different profile"

### **2. Astrology Service Intents**

#### **`generate_kundli`**
- **Description**: User wants to generate a kundli/horoscope
- **Workflow**: `GenerateKundliStep` (native LLM integration)
- **Features**:
  - Profile validation
  - Birth chart generation
  - Report creation
  - Artifact delivery

**Example User Messages:**
- "Generate my kundli"
- "I want my horoscope"
- "Create birth chart"
- "Show me my astrological chart"

#### **`query_kundli`**
- **Description**: User wants to query existing kundli data
- **Workflow**: Kundli query workflow
- **Features**: Data retrieval, analysis, and insights

**Example User Messages:**
- "What's in my kundli?"
- "Tell me about my chart"
- "Analyze my birth chart"

### **3. Prediction Service Intents**

#### **`subscribe_predictions`**
- **Description**: User wants to subscribe to astrological predictions
- **Workflow**: Subscription workflow
- **Features**: Plan selection, payment, activation

**Example User Messages:**
- "I want daily predictions"
- "Subscribe me to horoscopes"
- "Get predictions subscription"

#### **`unsubscribe_predictions`**
- **Description**: User wants to cancel prediction subscription
- **Workflow**: Unsubscription workflow
- **Features**: Confirmation, cancellation, refund processing

**Example User Messages:**
- "Cancel my subscription"
- "Stop predictions"
- "Unsubscribe from horoscopes"

### **4. General Service Intents**

#### **`general_qna`**
- **Description**: User asks general astrology questions
- **Workflow**: QnA workflow
- **Features**: LLM-powered responses, context awareness

**Example User Messages:**
- "What is a kundli?"
- "How does astrology work?"
- "Tell me about zodiac signs"
- "What are planetary positions?"

#### **`help`**
- **Description**: User requests assistance, menu, or capabilities
- **Workflow**: Help workflow
- **Features**: Feature overview, navigation, support

**Example User Messages:**
- "Help"
- "What can you do?"
- "Show me menu"
- "I need help"

#### **`unknown`**
- **Description**: System cannot classify user intent
- **Workflow**: Fallback workflow
- **Features**: Clarification, guidance, error recovery

## 🔧 Adding New Intents

### **Step 1: Define Intent Configuration**

Add your intent to `services/intent_config.py`:

```python
def _initialize_default_intents(self):
    # ... existing intents ...
    
    # Add your new intent
    self.register_intent(IntentConfig(
        intent_id="check_compatibility",
        description="User wants to check astrological compatibility with someone.",
        workflow_steps=["compatibility_check_native"],
        initial_step="compatibility_check_native",
    ))
```

### **Step 2: Create Workflow Step**

Implement your workflow step in `services/workflows/steps/`:

```python
from services.workflows.base import WorkflowStep, StepResult, StepAction
from pydantic import BaseModel

class CompatibilityState(BaseModel):
    """State for compatibility checking workflow."""
    person1_profile_id: Optional[str] = None
    person2_profile_id: Optional[str] = None
    compatibility_type: Optional[str] = None
    analysis_complete: bool = False

class CompatibilityCheckStep(WorkflowStep):
    def __init__(self):
        super().__init__("compatibility_check_native")
        self.workflow_id = "check_compatibility"
    
    async def execute(self, message: CanonicalRequestMessage, session: Session, workflow_context: WorkflowContext) -> StepResult:
        # Get current state
        state = CompatibilityState(**workflow_context.get("compatibility_state", {}))
        
        # Implement your workflow logic here
        # ...
        
        return StepResult(
            response=canonical_response,
            action=StepAction.CONTINUE,  # or COMPLETE, REPEAT, etc.
            context_updates={"compatibility_state": state.model_dump()}
        )
```

### **Step 3: Register Workflow Step**

Add your step to `services/workflows/setup.py`:

```python
def initialize_workflows():
    registry = get_workflow_registry()
    
    # Register your step
    registry.register_step(CompatibilityCheckStep())
    
    # Register workflow definition
    compatibility_workflow = WorkflowDefinition(
        workflow_id="check_compatibility",
        name="Check Compatibility",
        description="Astrological compatibility analysis",
        steps=["compatibility_check_native"],
        initial_step="compatibility_check_native"
    )
    registry.register_workflow(compatibility_workflow)
```

### **Step 4: Test Your Intent**

Run tests to ensure your intent works correctly:

```bash
# Test workflow execution
pytest tests/unit/test_workflow_engine.py -k "compatibility"

# Test intent classification
pytest tests/unit/test_router.py -k "compatibility"
```

## 🧠 Intent Classification System

### **LLM-Based Classification**

The system uses LLMs for intelligent intent recognition with context awareness:

**Classification Prompt Structure:**
```python
def _build_classification_prompt(self, content: str, session: Session) -> str:
    # Include conversation history
    recent_messages = session.conversation_history[-5:]
    
    # Include user context
    user_context = f"User has {len(session.profiles)} profiles"
    if session.current_profile_id:
        user_context += f", currently using profile {session.current_profile_id}"
    
    prompt = f"""
    Classify the user's intent from the following message:
    
    Message: "{content}"
    User Context: {user_context}
    Recent Conversation: {recent_messages}
    
    Available Intents:
    - add_profile: User wants to create a new astrological profile
    - generate_kundli: User wants to generate a kundli/horoscope
    - check_compatibility: User wants to check astrological compatibility
    - subscribe_predictions: User wants to subscribe to predictions
    - general_qna: User asks general astrology questions
    - help: User requests assistance or menu
    
    Respond with JSON: {{"intent": "intent_name", "confidence": 0.95}}
    """
    
    return prompt
```

### **Fallback Classification**

When LLM classification fails, the system falls back to rule-based classification:

```python
def _rule_based_classification(self, content: str) -> str:
    content_lower = content.lower()
    
    # Profile-related keywords
    if any(word in content_lower for word in ["profile", "birth", "create", "add"]):
        return "add_profile"
    
    # Kundli-related keywords
    if any(word in content_lower for word in ["kundli", "horoscope", "chart", "generate"]):
        return "generate_kundli"
    
    # Compatibility-related keywords
    if any(word in content_lower for word in ["compatibility", "match", "compare"]):
        return "check_compatibility"
    
    # Default to general QnA
    return "general_qna"
```

## 🔄 Intent-to-Workflow Mapping

### **1:1 Intent-to-Workflow Relationship**

Each intent maps to exactly one workflow:

```python
# Intent configuration automatically creates workflow mapping
intent_config = IntentConfig(
    intent_id="add_profile",           # Maps to workflow ID
    description="User wants to create a new astrological profile",
    workflow_steps=["add_profile_native"],  # Workflow step sequence
    initial_step="add_profile_native"       # Starting step
)

# This creates:
# - Workflow ID: "add_profile"
# - Workflow Name: "Add Profile" (auto-generated)
# - Step Sequence: ["add_profile_native"]
# - Initial Step: "add_profile_native"
```

### **Workflow Step Registration**

Steps are registered independently and can be reused across workflows:

```python
# Register individual steps
registry.register_step(AddProfileStep())
registry.register_step(GenerateKundliStep())
registry.register_step(CompatibilityCheckStep())

# Register workflows that use these steps
add_profile_workflow = WorkflowDefinition(
    workflow_id="add_profile",
    steps=["add_profile_native"],
    initial_step="add_profile_native"
)

compatibility_workflow = WorkflowDefinition(
    workflow_id="check_compatibility",
    steps=["compatibility_check_native"],
    initial_step="compatibility_check_native"
)
```

## 📊 Intent Analytics & Monitoring

### **Intent Distribution Tracking**

Monitor how users interact with different intents:

```python
class IntentAnalytics:
    def track_intent_classification(self, user_id: str, content: str, classified_intent: str, confidence: float):
        """Track intent classification for analytics."""
        analytics_data = {
            "user_id": user_id,
            "content": content,
            "classified_intent": classified_intent,
            "confidence": confidence,
            "timestamp": datetime.utcnow()
        }
        
        # Store analytics data
        self.analytics_dao.save_intent_classification(analytics_data)
```

### **Intent Performance Metrics**

Track classification accuracy and performance:

```python
class IntentMetrics:
    def calculate_classification_accuracy(self, time_period: str = "24h") -> Dict[str, float]:
        """Calculate intent classification accuracy."""
        # Implementation for accuracy calculation
        pass
    
    def get_intent_distribution(self, time_period: str = "24h") -> Dict[str, int]:
        """Get distribution of classified intents."""
        # Implementation for distribution calculation
        pass
```

## 🧪 Testing Intents

### **Unit Testing**

Test individual intent classification:

```python
def test_add_profile_intent_classification():
    router = LunaRouter()
    session = Session(user_id="test_user")
    
    # Test various ways to express add_profile intent
    test_messages = [
        "I want to create a new profile",
        "Add my birth details",
        "Create profile for me",
        "I need to set up my astrological profile"
    ]
    
    for message in test_messages:
        intent = await router.classify_intent(message, session)
        assert intent == "add_profile", f"Failed to classify: {message}"
```

### **Integration Testing**

Test complete intent-to-workflow flow:

```python
def test_add_profile_workflow_integration():
    channels_service = ChannelsService()
    message = CanonicalRequestMessage(
        user_id="test_user",
        channel_type=ChannelType.TELEGRAM,
        channel_user_id="123",
        content="I want to create a new profile",
        content_type=ContentType.TEXT
    )
    
    # Process message through complete flow
    response = await channels_service.process_incoming_message(message)
    
    # Verify response indicates workflow started
    assert "profile" in response.content.lower()
    assert response.metadata.get("workflow_id") == "add_profile"
```

## 🚀 Best Practices

### **Intent Design Principles**

1. **Clear and Specific**: Each intent should have a clear, specific purpose
2. **User-Centric**: Focus on what users want to accomplish, not implementation details
3. **Consistent Naming**: Use consistent naming patterns (e.g., `verb_noun` format)
4. **Mutually Exclusive**: Intents should be distinct and not overlap significantly

### **Description Writing Guidelines**

1. **User Perspective**: Write from the user's point of view
2. **Action-Oriented**: Focus on what the user wants to do
3. **Specific Examples**: Include examples of user messages that would trigger the intent
4. **Clear Boundaries**: Make it clear what does and doesn't belong to this intent

### **Workflow Integration**

1. **Single Responsibility**: Each workflow should handle one main user goal
2. **Progressive Disclosure**: Collect information progressively, not all at once
3. **Error Handling**: Provide clear guidance when things go wrong
4. **Completion Indicators**: Clearly indicate when workflows are complete


---

This intent management system provides a robust foundation for understanding user needs and routing them to appropriate workflows, ensuring a smooth and intelligent user experience across all Luna Server interactions.
