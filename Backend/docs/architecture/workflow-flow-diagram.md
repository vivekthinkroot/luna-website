# Workflow Flow Diagram

This document provides a comprehensive visual representation of all possible workflow paths in the Luna system.

## Complete Workflow Architecture

The diagram below illustrates all possible flows between different workflows and steps in the system, including:
- Main entry points through the router/intent classifier
- Profile Resolution flow
- Add Profile flow
- Generate Kundli workflow
- Profile QnA workflow
- Main Menu flow
- Unknown/fallback flow

```mermaid
flowchart TD
    %% Main Entry Points
    START["User Message"] --> RouterID["Router/Intent Classifier"]
    RouterID --> |"Generate Kundli"| GenerateKundliWF["Workflow: GENERATE_KUNDLI"]
    RouterID --> |"Astro Consultation"| ProfileQnaWF["Workflow: PROFILE_QNA"]
    RouterID --> |"Main Menu"| MainMenuWF["Workflow: MAIN_MENU"]
    RouterID --> |"Unknown Intent"| UnknownWF["Workflow: UNKNOWN"]
    
    %% External Events Handling
    ExternalEvent["External Event\n(payment_success, etc.)"] --> EventHandlerEngine["Event Handler\nEngine"]
    EventHandlerEngine --> |"Find waiting workflow"| ResumeWorkflow["Resume Workflow"]
    ResumeWorkflow --> |"Step.on_event()"| HandleStepEvent["Handle Event in Step"]
    HandleStepEvent --> |"Continue workflow"| WorkflowContinue["Continue Workflow Execution"]
    
    %% Main Menu Flow
    MainMenuWF --> MainMenuStep["MainMenuStep"]
    MainMenuStep --> |"Quick Reply: Generate Kundli"| GenerateKundliWF
    MainMenuStep --> |"Quick Reply: Astro Consultation"| ProfileQnaWF
    MainMenuStep --> |"StepAction: COMPLETE"| END["End Workflow"]
    
    %% Unknown Workflow Flow
    UnknownWF --> UnknownFallbackStep["UnknownFallbackStep"]
    UnknownFallbackStep --> |"First message: Welcome"| ShowWelcome["Show Welcome Message"]
    UnknownFallbackStep --> |"Not first message: Fallback"| ShowFallback["Show Fallback Message"]
    ShowWelcome --> |"StepAction: COMPLETE"| END
    ShowFallback --> |"StepAction: COMPLETE"| END
    
    %% Common Profile Resolution Flow (used by both main workflows)
    subgraph ProfileResolutionFlow["Profile Resolution Flow"]
        ProfileResolutionStep["ProfileResolutionStep"]
        ProfileResolutionStep --> |"Current profile exists"| ConfirmCurrentProfile["Confirm Current Profile"]
        ProfileResolutionStep --> |"No current profile"| ListProfiles["List Available Profiles"]
        
        ConfirmCurrentProfile --> |"Quick Reply: Use current"| UseCurrentProfile["Use Current Profile"]
        ConfirmCurrentProfile --> |"Quick Reply: Choose another"| ListProfiles
        ConfirmCurrentProfile --> |"Quick Reply: Create new"| CreateNewProfile
        
        ListProfiles --> |"Quick Reply: Select profile"| SelectExistingProfile["Select Existing Profile"]
        ListProfiles --> |"Quick Reply: Create new"| CreateNewProfile["Create New Profile"]
        
        UseCurrentProfile --> |"StepAction: ADVANCE_NOW\nContext: profile_selected=true"| ProfileResolutionComplete["Profile Resolution Complete"]
        SelectExistingProfile --> |"StepAction: ADVANCE_NOW\nContext: profile_selected=true"| ProfileResolutionComplete
        
        CreateNewProfile --> |"StepAction: JUMP\nTo: PROFILE_ADDITION\nWorkflow: GENERATE_KUNDLI"| AddProfileStep
    end
    
    %% Add Profile Flow
    subgraph AddProfileFlow["Add Profile Flow"]
        AddProfileStep["AddProfileStep"]
        AddProfileStep --> |"Basic Details Stage"| CollectBasicDetails["Collect Basic Details"]
        CollectBasicDetails --> |"Complete basic details"| LocationResolution["Location Resolution"]
        
        LocationResolution --> |"Single exact match"| AutoResolveLocation["Auto-resolve Location"]
        LocationResolution --> |"Multiple matches"| AskForLocationSelection["Ask for Location Selection"]
        LocationResolution --> |"No matches"| AskForBirthPlace["Ask for New Birth Place"]
        
        AskForLocationSelection --> |"User selects location"| LocationSelected["Location Selected"]
        AskForBirthPlace --> CollectBasicDetails
        
        AutoResolveLocation --> ConfirmationStage["Confirmation Stage"]
        LocationSelected --> ConfirmationStage
        
        ConfirmationStage --> |"User confirms"| CreateProfile["Create Profile"]
        ConfirmationStage --> |"User edits"| HandleEdits["Handle Profile Edits"]
        
        HandleEdits --> |"Birth place changed"| LocationResolution
        HandleEdits --> |"Other fields changed"| CollectBasicDetails
        HandleEdits --> |"Multiple fields changed"| CollectBasicDetails
        
        CreateProfile --> |"StepAction: CONTINUE\nProfile created"| AddProfileComplete["Add Profile Complete"]
    end
    
    %% Generate Kundli Workflow
    subgraph GenerateKundliWorkflow["Generate Kundli Workflow"]
        GenerateKundliWF --> ProfileResolutionStep
        AddProfileComplete --> |"StepAction: CONTINUE"| KundliGenerationStep["KundliGenerationStep"]
        ProfileResolutionComplete --> |"Next in workflow\nWith _handoff context"| KundliGenerationStep
        
        KundliGenerationStep --> |"Generate Kundli Report"| KundliGenerated["Kundli Generated"]
        KundliGenerated --> |"StepAction: COMPLETE"| END
        KundliGenerationStep --> |"StepAction: WAIT\nfor external event"| WaitingState["Workflow in Waiting State"]
    end
    
    %% Profile QnA Workflow
    subgraph ProfileQnAWorkflow["Profile QnA Workflow"]
        ProfileQnaWF --> ProfileResolutionStep
        ProfileResolutionComplete --> |"Next in workflow\nWith _handoff context"| ProfileQnAStep["ProfileQnAStep"]
        
        ProfileQnAStep --> |"First interaction"| WelcomeQnA["Show Welcome & Ask for Question"]
        WelcomeQnA --> |"StepAction: REPEAT\nUpdate conversation context"| ContinueQnA
        
        ProfileQnAStep --> |"Ongoing interaction"| ProcessQuestion["Process Astrological Question"]
        ProcessQuestion --> |"LLM Response"| GenerateAnswer["Generate Astrological Answer"]
        
        GenerateAnswer --> |"Switch profile detected\nLLM reasoning"| SwitchProfileIntent["Switch Profile Intent"]
        GenerateAnswer --> |"Normal answer"| ContinueQnA["Continue QnA"]
        
        SwitchProfileIntent --> |"StepAction: JUMP\nTo: PROFILE_RESOLUTION"| ProfileResolutionStep
        
        ContinueQnA --> |"Quick Reply: Switch profile"| SwitchProfileQR["User Wants to Switch Profile"]
        SwitchProfileQR --> |"StepAction: JUMP\nTo: PROFILE_RESOLUTION"| ProfileResolutionStep
        
        ContinueQnA --> |"StepAction: REPEAT\nUpdate conversation context"| ProfileQnAStep
        
        %% Error handling path
        ProfileQnAStep --> |"LLM Error"| ErrorHandling["Error Handling"]
        ErrorHandling --> |"StepAction: REPEAT"| ProfileQnAStep
    end
    
    %% Connect flows to the start and end states
    AddProfileStep --- CreateNewProfile
```

## Key Workflow Features

1. **Non-deterministic Flows**:
   - LLM reasoning for intent detection and profile switching creates dynamic paths
   - User selections via quick replies create branching paths
   - Error handling and fallbacks provide alternative routes

2. **Workflow Transitions**:
   - Steps can advance linearly (CONTINUE), immediately (ADVANCE_NOW), repeat for multi-turn interactions (REPEAT), or jump to other steps/workflows (JUMP)
   - StepAction.WAIT allows workflows to pause execution and wait for external events
   - Workflows can transition to other workflows with context preservation using _handoff mechanism
   - State is maintained across transitions for coherent user experience

3. **Multi-stage Operations**:
   - Profile creation involves multiple stages with data validation
   - Profile Q&A maintains conversation history for context
   - Location resolution has specialized handling for various match scenarios

4. **Context Management**:
   - The workflow engine manages context across steps and workflows
   - Structured handoffs between components maintain state through explicit _handoff context
   - Each workflow maintains its own contextual state that persists across user interactions
   - Session data persists critical information between user interactions

5. **Event Handling**:
   - Workflows can pause execution (StepAction.WAIT) to wait for external events
   - External events (like payment callbacks) can resume paused workflows
   - The on_event handler in steps processes external events when workflows are in waiting state

This diagram serves as a reference for understanding the complete flow of user interactions through the system.
