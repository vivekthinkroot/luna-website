# Slash Command Workflow

## Overview

The slash command workflow provides users with a main menu interface that can be invoked at any time during a conversation. This allows users to easily navigate between different features and workflows without having to remember specific commands or phrases.

## Supported Commands

The following slash commands are supported (case-insensitive):

- `/luna` - Main menu
- `/menu` - Main menu  
- `/help` - Main menu

## How It Works

### 1. Command Detection

When a user sends a message, the router first checks if it's a slash command during the intent classification process. The `_is_slash_command()` method:

- Strips whitespace from the message content
- Converts to lowercase for case-insensitive matching
- Checks if the content starts with any of the supported slash commands

### 2. Intent Classification Integration

Slash commands are detected within the existing `_classify_intent()` method, maintaining the original flow:

1. **Quick Reply Check**: First checks if the message has a selected quick reply
2. **Slash Command Check**: Then checks if it's a slash command
3. **LLM Classification**: Falls back to LLM-based intent classification if neither applies

If a slash command is detected, the method returns `"main_menu"` as the intent, which then follows the normal workflow routing process.

### 3. Normal Workflow Routing

Once the intent is classified (including slash commands), the message follows the standard workflow execution path:

- Intent is stored in the session
- Message is routed to the workflow engine
- Workflow engine executes the `main_menu` workflow
- MainMenuStep presents the menu options
- Workflow completes after showing the menu

## Current Menu Options

1. **Generate my Kundli** - Routes to the kundli generation workflow
2. **Astro Consultation** - Routes to the profile Q&A workflow

## Implementation Details

### Workflow Structure

```
main_menu
└── main_menu_step (single step, completes immediately)
```

### Key Components

- **Workflow ID**: `main_menu`
- **Step ID**: `main_menu_step`
- **Intent ID**: `main_menu`
- **Action**: `COMPLETE` (workflow completes after showing menu)

### Router Integration

The slash command detection is integrated into the `LunaRouter._classify_intent()` method:

```python
async def _classify_intent(self, message: CanonicalRequestMessage, session: Session) -> str:
    try:
        # Check for deterministic quick reply intent first
        if message.selected_reply and message.selected_reply.has_valid_format():
            # ... quick reply handling ...
            
        # Check if this is a slash command
        if self._is_slash_command(message):
            logger.info(f"Slash command detected, returning main_menu intent: {message.content}")
            return "main_menu"
            
        # Fall back to LLM-based classification
        # ... LLM classification logic ...
        
    except Exception as e:
        return "unknown"
```

This approach ensures that:
- The original flow is preserved
- Slash commands are detected early in the classification process
- The intent is properly stored in the session
- All messages follow the same workflow execution path

## Adding New Menu Options

To add new menu options:

1. **Add the workflow** to `services/workflows/ids.py`:
   ```python
   class Workflows(str, Enum):
       # ... existing workflows
       NEW_FEATURE = "new_feature"
   ```

2. **Update the main menu step** in `services/workflows/steps/main_menu_step.py`:
   ```python
   MAIN_MENU_QUICK_REPLIES = [
       # ... existing options
       QuickReplyOption.build(
           Workflows.NEW_FEATURE.value, "new_feature", "New Feature"
       ),
   ]
   ```

3. **Register the new workflow** in the intent configuration and workflow setup

## Benefits

- **Always Accessible**: Users can access the main menu at any time
- **Context Independent**: Works regardless of current conversation state
- **Fast Navigation**: Direct routing without LLM processing
- **User Friendly**: Familiar slash command interface
- **Extensible**: Easy to add new menu options

## Testing

The implementation includes comprehensive tests:

- **Unit tests** for the main menu step (`tests/unit/test_main_menu_workflow.py`)
- **Unit tests** for slash command detection (`tests/unit/test_slash_command_detection.py`)

Run tests with:
```bash
pytest tests/unit/test_main_menu_workflow.py -v
pytest tests/unit/test_slash_command_detection.py -v
```

## Future Enhancements

- **Custom slash commands** for power users
- **Context-aware menu options** based on user preferences
- **Keyboard shortcuts** for desktop/web interfaces
- **Voice commands** for voice-enabled channels
