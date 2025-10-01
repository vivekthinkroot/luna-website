"""
Profile resolution step: confirms/chooses/creates a profile before proceeding.

All user-facing copy is consolidated below for clarity and easy iteration.
"""

from typing import Any, Dict, List
from uuid import UUID

from dao.profiles import Profile, ProfileDAO
from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps, Workflows
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, QuickReplyOption
from utils.sessions import Session

logger = get_logger()

# ===== User-facing text constants =====

# Prompts and messages
TEXT_PROMPT_PICK_PROFILE = "Alright, please pick the person whose astrological profile you want to use for this conversation.\n\nOr, add a new profile if needed."

TEXT_CREATE_NEW = (
    "Sure then, let's create a new profile."
    "\n\nPlease share the person's:\n- Name\n- Date of Birth\n- Time of Birth\n- Place of Birth\n- Gender\n- Relationship to you"
)
TEXT_PROFILE_SELECTED = "Alright, I'm referring to *{formatted_name}*'s astrological profile for this conversation."
TEXT_INVALID_PROFILE_ID = "That selection looks invalid. Please choose again."
TEXT_NO_PROFILES = (
    "You don't have any saved profiles yet. Let's add one now."
    "\n\nPlease share the person's:\n- Name\n- Date of Birth\n- Time of Birth\n- Place of Birth\n- Gender\n- Relationship to you"
)

TEXT_PROFILES_HEADER = "I found these profiles linked to your account:"
TEXT_PROFILES_FOOTER = "You can choose one or create a new profile."

# Quick-reply labels
QR_CHOOSE_ANOTHER = "Choose Profile"
QR_CREATE_NEW = "Add New Profile"


class ProfileResolutionStep(WorkflowStep):
    def __init__(self):
        super().__init__(Steps.PROFILE_RESOLUTION.value)
        self.profile_dao = ProfileDAO()
        self.workflow_id: str = "generate_kundli"

    # Format profile name (title case, cap at 20 characters with ellipsis)
    def _format_profile_name(self, name: str) -> str:
        formatted_name = name.title()
        if len(formatted_name) <= 20:
            return formatted_name
        return formatted_name[:17] + "..."

    def _build_quick_replies_for_existing(
        self,
        current_profile_name: str,
        all_profiles: List[Profile],
        current_profile_id: UUID,
    ) -> List[QuickReplyOption]:

        formatted_name = self._format_profile_name(current_profile_name)
        other_profiles_count = len(all_profiles) - 1

        options = [
            QuickReplyOption.build(
                self.workflow_id,
                "use_current",
                self._format_profile_name(f"{formatted_name}"),
            ),
        ]

        # Only show "choose another" if there are multiple other profiles
        if other_profiles_count > 1:
            options.append(
                QuickReplyOption.build(
                    self.workflow_id, "choose_another", QR_CHOOSE_ANOTHER
                )
            )
        elif other_profiles_count == 1:
            # If there's exactly one other profile, show its name with specific action
            other_profile = [
                p for p in all_profiles if p.profile_id != current_profile_id
            ][0]
            other_formatted_name = self._format_profile_name(
                other_profile.name or "Unnamed"
            )
            options.append(
                QuickReplyOption.build(
                    self.workflow_id,
                    "select_specific_profile",
                    f"{other_formatted_name}",
                    suffix=str(other_profile.profile_id),
                )
            )

        options.append(
            QuickReplyOption.build(self.workflow_id, "create_new", QR_CREATE_NEW)
        )

        return options

    def _build_quick_replies_for_selection(
        self, profiles: List[Profile]
    ) -> List[QuickReplyOption]:
        options: List[QuickReplyOption] = []
        for index, p in enumerate(profiles, start=1):
            suffix = str(p.profile_id)
            label = f"{index}. {p.name or 'Unnamed'}"
            options.append(
                QuickReplyOption.build(
                    self.workflow_id,
                    "select_specific_profile",
                    self._format_profile_name(label),
                    suffix=suffix,
                )
            )
        options.append(
            QuickReplyOption.build(self.workflow_id, "create_new", QR_CREATE_NEW)
        )
        return options

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        # Use the actual workflow id for deterministic quick replies
        self.workflow_id = workflow_id

        # If a quick reply was chosen, handle it deterministically
        if message.selected_reply and message.selected_reply.has_valid_format():
            action = message.selected_reply.get_action()
            if action == "use_current" and session.current_profile_id:
                current_profile = self.profile_dao.get_profile_by_id(
                    str(session.current_profile_id)
                )
                if current_profile:
                    formatted_name = self._format_profile_name(
                        current_profile.name or "Unnamed"
                    )
                    response = message.create_text_response(
                        content=TEXT_PROFILE_SELECTED.format(
                            formatted_name=formatted_name
                        ),
                        metadata={"continue_multi_turn": False},
                    )
                else:
                    # not possible
                    pass
                # Let the engine move to the next step in the parent workflow, with a structured handoff
                # Place handoff into workflow context via context_updates
                return StepResult(
                    response=response,
                    action=StepAction.ADVANCE_NOW,
                    context_updates={
                        "_handoff": {
                            "profile_selected": True,
                            "profile_id": str(session.current_profile_id),
                        }
                    },
                )
            if action == "create_new":
                response = message.create_text_response(
                    content=TEXT_CREATE_NEW,
                    metadata={"continue_multi_turn": True},
                )
                return StepResult(
                    response=response,
                    action=StepAction.JUMP,
                    next_step_id=Steps.PROFILE_ADDITION.value,
                    # When creating new profile, transition to kundli generation workflow
                    next_workflow_id=Workflows.GENERATE_KUNDLI.value,
                )
            if action == "choose_another":
                profiles = self.profile_dao.get_profiles_for_user(session.user_id)
                if profiles:
                    names = [
                        f"{i+1}. {p.name or 'Unnamed'}" for i, p in enumerate(profiles)
                    ]
                    content = (
                        TEXT_PROFILES_HEADER
                        + "\n"
                        + "\n".join(names)
                        + "\n\n"
                        + TEXT_PROFILES_FOOTER
                    )
                    response = message.create_text_response(
                        content=content,
                        metadata={"continue_multi_turn": True},
                        reply_options=self._build_quick_replies_for_selection(profiles),
                    )
                    return StepResult(response=response, action=StepAction.REPEAT)
            if action == "select_specific_profile":
                pid = message.selected_reply.get_suffix()
                if pid:
                    try:
                        session.current_profile_id = UUID(pid)
                        selected_profile = self.profile_dao.get_profile_by_id(
                            str(session.current_profile_id)
                        )
                        if selected_profile:
                            # Format profile name (title case, cap at 20 characters with ellipsis)
                            def format_profile_name(name: str) -> str:
                                formatted_name = name.title()
                                if len(formatted_name) <= 20:
                                    return formatted_name
                                return formatted_name[:17] + "..."

                            formatted_name = format_profile_name(
                                selected_profile.name or "Unnamed"
                            )
                            response = message.create_text_response(
                                content=TEXT_PROFILE_SELECTED.format(
                                    formatted_name=formatted_name
                                ),
                                metadata={"continue_multi_turn": False},
                            )
                        else:
                            response = message.create_text_response(
                                content=TEXT_PROFILE_SELECTED.format(
                                    formatted_name="profile"
                                ),
                                metadata={"continue_multi_turn": False},
                            )
                        return StepResult(
                            response=response,
                            action=StepAction.ADVANCE_NOW,
                            context_updates={
                                "_handoff": {
                                    "profile_selected": True,
                                    "profile_id": str(session.current_profile_id),
                                }
                            },
                        )
                    except ValueError:
                        logger.warning(f"Invalid profile ID format: {pid}")
                        response = message.create_text_response(
                            content=TEXT_INVALID_PROFILE_ID,
                            metadata={"continue_multi_turn": True},
                        )
                        return StepResult(response=response, action=StepAction.REPEAT)

        # No quick reply or unrecognized; evaluate current context
        if session.current_profile_id:
            # Get current profile details
            current_profile = self.profile_dao.get_profile_by_id(
                str(session.current_profile_id)
            )
            if not current_profile:
                logger.error(f"Current profile {session.current_profile_id} not found")
                # Reset current profile and continue with normal flow
                session.current_profile_id = None
            else:
                # Get all profiles for this user to determine options
                all_profiles = self.profile_dao.get_profiles_for_user(session.user_id)

                # Format profile name for prompt (title case, cap at 20 characters with ellipsis)
                def format_profile_name(name: str) -> str:
                    formatted_name = name.title()
                    if len(formatted_name) <= 20:
                        return formatted_name
                    return formatted_name[:17] + "..."

                current_profile_name = current_profile.name or "Unnamed"
                formatted_name = format_profile_name(current_profile_name)

                # Show compact summary with profile name and ask to pick a profile
                response = message.create_text_response(
                    content=TEXT_PROMPT_PICK_PROFILE,
                    metadata={"continue_multi_turn": True},
                    reply_options=self._build_quick_replies_for_existing(
                        current_profile_name, all_profiles, session.current_profile_id
                    ),
                )
                return StepResult(response=response, action=StepAction.REPEAT)

        # If we get here, either no current profile was set or it was reset
        # No active profile: list existing or offer create
        profiles = self.profile_dao.get_profiles_for_user(session.user_id)
        if profiles:
            names = [f"{i+1}. {p.name or 'Unnamed'}" for i, p in enumerate(profiles)]
            content = (
                TEXT_PROFILES_HEADER
                + "\n"
                + "\n".join(names)
                + "\n\n"
                + TEXT_PROFILES_FOOTER
            )
            response = message.create_text_response(
                content=content,
                metadata={"continue_multi_turn": True},
                reply_options=self._build_quick_replies_for_selection(profiles),
            )
            return StepResult(response=response, action=StepAction.REPEAT)

        # No profiles at all: create new
        response = message.create_text_response(
            content=TEXT_CREATE_NEW,
            metadata={"continue_multi_turn": True},
        )
        return StepResult(
            response=response,
            action=StepAction.JUMP,
            next_step_id=Steps.PROFILE_ADDITION.value,
            # When creating new profile, transition to kundli generation workflow
            next_workflow_id=Workflows.GENERATE_KUNDLI.value,
        )
