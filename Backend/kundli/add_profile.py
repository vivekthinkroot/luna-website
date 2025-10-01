"""
Workflow-native implementation of the Add Profile flow.

This step replicates the behavior of `kundli.add_profile_handler.AddProfileHandler`,
including multi-stage collection, local location resolution with candidate
presentation/selection, confirmation, and profile creation.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, computed_field

from dao.geolocation import GeolocationDAO
from dao.profiles import ProfileDAO
from data.models import Gender, RelationshipType
from kundli.utils import get_sun_sign
from llms.client import LLMClient, LLMResponseType
from llms.models import LLMMessage, LLMMessageRole
from services.geolocation import (
    GeolocationService,
    LocationSearchResult,
)
from dao.cities import CityCandidate as LocationCandidate
from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps, Workflows
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, QuickReplyOption
from utils.sessions import Session

logger = get_logger()


class AddProfileStage(str, Enum):
    BASIC_DETAILS = "basic_details"
    LOCATION_RESOLUTION = "location_resolution"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class ProfileState(BaseModel):
    # Basic profile fields provided by the user
    name: Optional[str] = None
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_place: Optional[str] = None
    birth_location_id: Optional[int] = None
    gender: Optional[Gender] = None
    relationship: Optional[RelationshipType] = None

    @computed_field(return_type=Optional[datetime])
    @property
    def birth_datetime(self) -> Optional[datetime]:
        if self.birth_date and self.birth_time:
            return datetime.combine(
                self.birth_date, self.birth_time, tzinfo=timezone.utc
            )
        return None

    @property
    def has_all_basic_details(self) -> bool:
        return all(
            [
                self.name,
                self.birth_date,
                self.birth_time,
                self.birth_place,
                self.gender,
                self.relationship,
            ]
        )


class ProfileWorkflowContext(BaseModel):
    """Internal-only workflow context for the profile creation flow.

    This is never exposed to users or LLMs via `ProfileState`.
    """

    current_step: AddProfileStage = AddProfileStage.BASIC_DETAILS
    pending_location_candidates: Optional[LocationSearchResult] = None
    selected_location: Optional[LocationCandidate] = None
    confirmation_prompt_shown: bool = False

    model_config = {"from_attributes": True}


# Stage-specific LLM response models
class BasicDetailsLLMResponse(BaseModel):
    # Extracted fields (partial)
    name: Optional[str] = None
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_place: Optional[str] = None
    gender: Optional[Gender] = None
    relationship: Optional[RelationshipType] = None

    # Conversational response
    response_text: str


class LocationResolutionLLMResponse(BaseModel):
    # When user clarifies/chooses, set the selected ID
    selected_location_id: Optional[int] = None
    response_text: str


class ProfileEdits(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_place: Optional[str] = None
    gender: Optional[Gender] = None
    relationship: Optional[RelationshipType] = None


class ConfirmationLLMResponse(BaseModel):
    confirmed: Optional[bool] = None
    edits: Optional[ProfileEdits] = None
    # Set to true when the user indicates the birth place is wrong but does not provide a new value
    wants_birth_place_change: Optional[bool] = None
    response_text: str


# Prompts (kept local to this file)
BASIC_DETAILS_SYSTEM_PROMPT = (
    "You are a helpful assistant collecting profile details for kundli generation.\n"
    "Your job in this stage is ONLY to gather or clarify these fields: name, birth_date,"
    " birth_time (HH:MM 24h or with AM/PM), birth_place (city), gender (MALE/FEMALE/OTHER), and relationship (SELF/PARENT/CHILD/SIBLING/FRIEND/PARTNER/OTHER).\n"
    "- Use a friendly, natural tone.\n"
    "- Ask minimal, targeted questions to fill missing fields. If multiple fields are missing, list them in separate lines for easier reading.\n"
    "- Infer missing fields from the user's response ONLY if you accurately can (ex. relationship = child, if the user says the profile is for their son / daughter / child / etc.; another example is if the user says the profile is for their mother, then gender = female, etc.).\n"
    "- For birth_place, do not make any assumptions, use exactly what the user says.\n"
    "- Never mention internal steps.\n"
    "- Reply with a JSON object matching the BasicDetailsLLMResponse schema.\n"
    "Current known state (JSON): {state}\n"
)


LOCATION_RESOLUTION_SYSTEM_PROMPT = (
    "You are assisting the user to choose their birth location from a provided list.\n"
    "- If the user replies with a number (1, 2, ...), map it to the corresponding ID.\n"
    "- If the user describes the location in natural language, pick the matching option's ID.\n"
    "- If unclear, ask a short clarifying question.\n"
    "- Reply with JSON matching LocationResolutionLLMResponse.\n"
    "Available options mapping (use this to set selected_location_id):\n{location_candidates}\n"
)


CONFIRMATION_SYSTEM_PROMPT = (
    "You are confirming the final profile details with the user.\n"
    "- If the user says yes / confirm / ok / anything affirmative, set confirmed=true.\n"
    "- If the user says no / wants to edit, set confirmed=false, and provide edits fields with the new values that the user provided.\n"
    "- If the user says their birth place is wrong but doesn't provide a new one, set wants_birth_place_change=true and do NOT set edits.birth_place.\n"
    "- Use a friendly, concise response.\n"
    "- Reply with JSON matching ConfirmationLLMResponse.\n"
    "Current state (JSON): {state}\n"
)


# Response messages organized by category
# Error messages
ERROR_LLM_PROCESSING_RETRY = "LLM processing failed. Check logs for details."
ERROR_GENERAL = "I'm sorry, something went wrong. please try again."

# Location resolution messages
LOCATION_NOT_FOUND = "I couldn't find any locations matching '{birth_place}'. Please check the location name."
LOCATION_NO_MATCHES = "No locations found for '{search_term}'."
LOCATION_CANDIDATES_TEMPLATE = (
    "{exact_matches_section}"
    "{fuzzy_matches_section}"
    "\nPlease select the correct location (you can say '1', '2', etc. or describe which is the right one)."
)

# Basic details collection messages
BASIC_DETAILS_ASK_BIRTH_PLACE = "Please share the city of birth for this profile."
BASIC_DETAILS_UPDATE_CONFIRMATION = (
    "I've updated the details. Is there anything else you'd like to update?"
)

# Profile confirmation messages
PROFILE_CONFIRMATION_TEMPLATE = (
    "Great! Here's a summary of the profile:\n\n"
    "👤 Name: {name}\n"
    "📅 Birth Date: {birth_date}\n"
    "🕐 Birth Time: {birth_time}\n"
    "📍 Birth Place: {birth_place}{timezone_info}\n"
    "⚧ Gender: {gender}\n"
    "💑 Relationship: {relationship}\n"
    "\nPlease confirm if all details are correct."
)
PROFILE_NOT_SET_VALUE = "Not set"


PROFILE_CONFIRMATION_NUDGE = "Please confirm if all details are correct. Type 'yes' to proceed or 'no' to make changes."

# Profile creation success message template
PROFILE_CREATION_SUCCESS_TEMPLATE = (
    "Perfect! I've saved {profile_name}'s profile successfully."
    "\n\nI can now generate the detailed Vedic natal birth chart (kundli) for {profile_name}."
    "\n\nWould you like to proceed?"
)

# Quick reply options for user interactions
# Note: These are now generated dynamically based on current workflow context
# to avoid cross-workflow contamination


class AddProfileStep(WorkflowStep):
    """
    Workflow step that manages the complete Add Profile conversation using
    a finite state machine semantics
    """

    def __init__(self):
        # Keep the same step id that setup registers in the workflow definition
        super().__init__(Steps.PROFILE_ADDITION.value)
        self.llm_client = LLMClient()
        self.profiles_dao = ProfileDAO()
        self.geolocation_dao = GeolocationDAO()
        # This will be populated from workflow_context when execute is called
        self.workflow_id: str = "add_profile"

    def _convert_birth_datetime_to_utc(
        self, birth_datetime: Optional[datetime], birth_location_id: Optional[int]
    ) -> Optional[datetime]:
        """
        Convert birth_datetime from local timezone to UTC for storage.

        The birth_datetime represents the time in the local timezone of the birth location.
        We need to convert this to UTC for proper storage in the database.

        Args:
            birth_datetime: The birth datetime in local timezone
            birth_location_id: The ID of the birth location

        Returns:
            The datetime converted to UTC, or the original datetime if conversion fails
        """
        if not birth_datetime or not birth_location_id:
            return birth_datetime

        try:
            location = self.geolocation_dao.get_location_by_id(birth_location_id)
            if location and location.timezone:
                # Convert the local time to UTC for storage
                tz = ZoneInfo(location.timezone)
                # First, localize the datetime to the location's timezone
                localized_datetime = birth_datetime.replace(tzinfo=tz)
                # Then convert to UTC
                utc_datetime = localized_datetime.astimezone(timezone.utc)
                logger.debug(
                    f"Converted birth_datetime from {location.timezone} local time {birth_datetime} to UTC: {utc_datetime}"
                )
                return utc_datetime
        except Exception as e:
            logger.warning(
                f"Failed to convert birth_datetime from local timezone to UTC: {e}. Using original datetime."
            )

        return birth_datetime

    def _get_profile_confirmation_reply_options(self) -> List[QuickReplyOption]:
        """Get profile confirmation quick reply options using current workflow ID."""
        return [
            QuickReplyOption.build(
                self.workflow_id, "confirm_profile_yes", "Yes, looks good"
            ),
            QuickReplyOption.build(
                self.workflow_id, "confirm_profile_no", "No, make changes"
            ),
        ]

    def _get_basic_details_update_reply_options(self) -> List[QuickReplyOption]:
        """Get basic details update quick reply options using current workflow ID."""
        return [
            QuickReplyOption.build(self.workflow_id, "details_done", "Looks good"),
            QuickReplyOption.build(
                self.workflow_id, "details_edit", "Need more changes"
            ),
        ]

    def _get_profile_creation_success_reply_options(self) -> List[QuickReplyOption]:
        """Get profile creation success quick reply options using current workflow ID."""
        return [
            QuickReplyOption.build(
                Workflows.GENERATE_KUNDLI.value,
                "confirm_kundli_yes",
                "Yes, let's do it now",
            ),
            QuickReplyOption.build(
                self.workflow_id, "confirm_kundli_no", "No, I'll do it later"
            ),
        ]

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        try:
            # Extract the current workflow ID from the workflow context
            # This is the actual workflow (e.g., "add_profile", "generate_kundli")
            self.workflow_id = workflow_id

            # Consume structured handoff if a profile was already selected
            handoff = (
                workflow_context.get("_handoff")
                if isinstance(workflow_context, dict)
                else None
            )
            if handoff and isinstance(handoff, dict):
                profile_selected = handoff.get("profile_selected")
                selected_profile_id = handoff.get("profile_id")
                if profile_selected and selected_profile_id:
                    try:
                        # Normalize and validate the selected profile
                        pid = str(UUID(str(selected_profile_id)))
                        profile = self.profiles_dao.get_profile_by_id(pid)
                        if profile:
                            # Set session profile for downstream steps
                            session.current_profile_id = profile.profile_id
                            # Clear the handoff and immediately advance to next step
                            noop_response = message.create_text_response(
                                content="",
                                metadata={"internal_noop": True},
                            )
                            return StepResult(
                                response=noop_response,
                                action=StepAction.ADVANCE_NOW,
                                context_updates={"_handoff": None},
                            )
                    except Exception:
                        # If parsing/validation fails, fall back to normal add-profile flow
                        pass

            # Load state from workflow context
            state_dict = workflow_context.get("profile_state", {}) or {}
            current_state = ProfileState(**state_dict) if state_dict else ProfileState()

            # Load internal workflow context
            wf_ctx_dict = workflow_context.get("profile_workflow", {}) or {}
            workflow_ctx = (
                ProfileWorkflowContext(**wf_ctx_dict)
                if wf_ctx_dict
                else ProfileWorkflowContext()
            )

            logger.info(
                "AddProfileStep.execute start | user=%s stage=%s | msg_len=%s",
                session.user_id,
                workflow_ctx.current_step.value,
                len(message.content) if isinstance(message.content, str) else None,
            )
            logger.debug(
                "State before handling | name=%s date=%s time=%s place=%s loc_id=%s gender=%s relationship=%s",
                current_state.name,
                current_state.birth_date,
                current_state.birth_time,
                current_state.birth_place,
                current_state.birth_location_id,
                (
                    getattr(current_state.gender, "value", None)
                    if current_state.gender
                    else None
                ),
                (
                    getattr(current_state.relationship, "value", None)
                    if current_state.relationship
                    else None
                ),
            )

            # Route by current stage and invoke stage-specific LLM/policies
            if workflow_ctx.current_step == AddProfileStage.BASIC_DETAILS:
                logger.info(
                    "Routing to BASIC_DETAILS | user=%s",
                    session.user_id,
                )
                return await self._stage_basic_details(
                    message=message,
                    session=session,
                    state=current_state,
                    workflow_ctx=workflow_ctx,
                )

            if workflow_ctx.current_step == AddProfileStage.LOCATION_RESOLUTION:
                logger.info(
                    "Routing to LOCATION_RESOLUTION | user=%s | pending_candidates=%s",
                    session.user_id,
                    (
                        workflow_ctx.pending_location_candidates.total_results
                        if workflow_ctx.pending_location_candidates
                        else 0
                    ),
                )
                return await self._stage_location_resolution(
                    message=message,
                    session=session,
                    state=current_state,
                    workflow_ctx=workflow_ctx,
                )

            if workflow_ctx.current_step == AddProfileStage.CONFIRMATION:
                logger.info(
                    "Routing to CONFIRMATION | user=%s",
                    session.user_id,
                )
                return await self._stage_confirmation(
                    message=message,
                    session=session,
                    state=current_state,
                    workflow_ctx=workflow_ctx,
                )

            # Fallback safety
            logger.warning(
                f"Unexpected workflow step {workflow_ctx.current_step}; defaulting to BASIC_DETAILS"
            )
            workflow_ctx.current_step = AddProfileStage.BASIC_DETAILS
            return await self._stage_basic_details(
                message=message,
                session=session,
                state=current_state,
                workflow_ctx=workflow_ctx,
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in AddProfileStep for user {session.user_id}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return self._create_error_result(message, ERROR_GENERAL)

    async def _get_basic_details_llm_response(
        self,
        state: ProfileState,
        message: CanonicalRequestMessage,
        session: Session,
    ):
        logger.debug(
            "LLM(BASIC_DETAILS) request | user=%s | have=[name=%s,date=%s,time=%s,place=%s,gender=%s,relationship=%s]",
            session.user_id,
            bool(state.name),
            bool(state.birth_date),
            bool(state.birth_time),
            bool(state.birth_place),
            bool(state.gender),
            bool(state.relationship),
        )
        message_history = self._get_conversation_history(session)
        system_msg = LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=BASIC_DETAILS_SYSTEM_PROMPT.format(state=state.model_dump_json()),
        )
        messages = [system_msg] + message_history

        return await self.llm_client.get_response(
            messages=messages,
            temperature=0.3,
            auto=True,
            response_model=BasicDetailsLLMResponse,
        )

    async def _get_location_resolution_llm_response(
        self,
        candidates: LocationSearchResult,
        message: CanonicalRequestMessage,
        session: Session,
    ):
        logger.debug(
            "LLM(LOCATION_RESOLUTION) request | user=%s | search_term=%s | exact=%s fuzzy=%s",
            session.user_id,
            candidates.search_term,
            len(candidates.exact_matches),
            len(candidates.fuzzy_matches),
        )
        message_history = self._get_conversation_history(session)
        candidates_text = self._format_location_candidates_for_llm(candidates)
        system_msg = LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=LOCATION_RESOLUTION_SYSTEM_PROMPT.format(
                location_candidates=candidates_text
            ),
        )
        messages = [system_msg] + message_history

        return await self.llm_client.get_response(
            messages=messages,
            temperature=0.2,
            auto=True,
            response_model=LocationResolutionLLMResponse,
        )

    async def _get_confirmation_llm_response(
        self,
        state: ProfileState,
        message: CanonicalRequestMessage,
        session: Session,
    ):
        logger.debug(
            "LLM(CONFIRMATION) request | user=%s | name=%s date=%s time=%s place=%s gender=%s relationship=%s",
            session.user_id,
            state.name,
            state.birth_date,
            state.birth_time,
            state.birth_place,
            getattr(state.gender, "value", None) if state.gender else None,
            getattr(state.relationship, "value", None) if state.relationship else None,
        )
        history_messages = self._get_conversation_history(session)
        system_msg = LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=CONFIRMATION_SYSTEM_PROMPT.format(state=state.model_dump_json()),
        )
        user_msg = LLMMessage(role=LLMMessageRole.USER, content=message.content)
        messages = [system_msg] + history_messages + [user_msg]

        return await self.llm_client.get_response(
            messages=messages,
            temperature=0.2,
            auto=True,
            response_model=ConfirmationLLMResponse,
        )

    def _get_conversation_history(
        self, session: Session, limit: int = 10
    ) -> list[LLMMessage]:
        """Get recent conversation history as LLM messages."""
        history = (
            session.conversation_history[-limit:]
            if session.conversation_history
            else []
        )
        messages: list[LLMMessage] = []
        for turn in history:
            role = (
                LLMMessageRole.USER if turn.role == "user" else LLMMessageRole.ASSISTANT
            )
            messages.append(LLMMessage(role=role, content=turn.content))
        return messages

    # Stage handlers
    async def _stage_basic_details(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        state: ProfileState,
        workflow_ctx: ProfileWorkflowContext,
    ) -> StepResult:
        # Compute missing fields snapshot
        missing: List[str] = []
        if not state.name:
            missing.append("name")
        if not state.birth_date:
            missing.append("birth_date")
        if not state.birth_time:
            missing.append("birth_time")
        if not state.birth_place:
            missing.append("birth_place")
        if not state.gender:
            missing.append("gender")
        if not state.relationship:
            missing.append("relationship")
        logger.debug("BASIC_DETAILS | user=%s | missing=%s", session.user_id, missing)

        llm_response = await self._get_basic_details_llm_response(
            state=state, message=message, session=session
        )
        if (
            llm_response.response_type == LLMResponseType.ERROR
            or not llm_response.object
        ):
            logger.error(
                "LLM(BASIC_DETAILS) error | user=%s | response_type=%s",
                session.user_id,
                llm_response.response_type,
            )
            return self._create_error_result(message, ERROR_LLM_PROCESSING_RETRY)

        llm_obj: BasicDetailsLLMResponse = llm_response.object  # type: ignore[assignment]

        # Apply extracted fields
        logger.debug(
            "BASIC_DETAILS LLM extracted | user=%s | name=%s date=%s time=%s place=%s gender=%s relationship=%s",
            session.user_id,
            llm_obj.name,
            llm_obj.birth_date,
            llm_obj.birth_time,
            llm_obj.birth_place,
            getattr(llm_obj.gender, "value", None) if llm_obj.gender else None,
            (
                getattr(llm_obj.relationship, "value", None)
                if llm_obj.relationship
                else None
            ),
        )
        if llm_obj.name is not None:
            state.name = llm_obj.name
        if llm_obj.birth_date is not None:
            state.birth_date = llm_obj.birth_date
        if llm_obj.birth_time is not None:
            state.birth_time = llm_obj.birth_time
        if llm_obj.birth_place is not None:
            # If place changed, reset location id
            if state.birth_place != llm_obj.birth_place:
                logger.info(
                    "BASIC_DETAILS | user=%s | birth_place changed '%s' -> '%s' | resetting birth_location_id",
                    session.user_id,
                    state.birth_place,
                    llm_obj.birth_place,
                )
                state.birth_location_id = None
            state.birth_place = llm_obj.birth_place
        if llm_obj.gender is not None:
            state.gender = llm_obj.gender
        if llm_obj.relationship is not None:
            state.relationship = llm_obj.relationship

        # Only proceed if we definitively have all required fields (deterministic check)
        ready_to_resolve = state.has_all_basic_details
        if ready_to_resolve and state.birth_place:
            # Kick off location resolution (deterministic)
            logger.info(
                "Transition -> LOCATION_RESOLUTION | user=%s | birth_place=%s",
                session.user_id,
                state.birth_place,
            )
            return self._start_location_resolution(
                birth_place=state.birth_place,
                state=state,
                workflow_ctx=workflow_ctx,
                session=session,
                message=message,
            )

        # Continue collecting details
        logger.debug(
            "BASIC_DETAILS continue | user=%s | response_len=%s",
            session.user_id,
            len(llm_obj.response_text) if llm_obj.response_text else 0,
        )
        response = message.create_text_response(
            content=llm_obj.response_text,
            metadata={"continue_multi_turn": True},
        )
        return StepResult(
            response=response,
            action=StepAction.REPEAT,
            context_updates={
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            },
        )

    def _start_location_resolution(
        self,
        birth_place: str,
        state: ProfileState,
        workflow_ctx: ProfileWorkflowContext,
        session: Session,
        message: CanonicalRequestMessage,
    ) -> StepResult:
        logger.info(f"User {session.user_id} resolving location: {birth_place}")

        location_result = self._resolve_birth_location(birth_place)
        logger.debug(
            f"User {session.user_id} found {location_result.total_results} location matches"
        )
        logger.debug(
            "Location matches | user=%s | exact_ids=%s | fuzzy_ids=%s",
            session.user_id,
            [loc.id for loc in location_result.exact_matches],
            [loc.id for (loc, _) in location_result.fuzzy_matches],
        )

        if location_result.total_results == 0:
            # No matches found - stay in BASIC_DETAILS
            logger.warning(
                f"User {session.user_id} no location matches for: {birth_place}"
            )
            response_text = LOCATION_NOT_FOUND.format(birth_place=birth_place)
            workflow_ctx.current_step = AddProfileStage.BASIC_DETAILS
            context_updates = {
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            }

        elif (
            location_result.total_results == 1
            and len(location_result.exact_matches) == 1
            and len(location_result.fuzzy_matches) == 0
        ):
            # Single exact match - auto-resolve and move to confirmation
            selected_location = location_result.exact_matches[0]
            logger.info(
                f"User {session.user_id} auto-selected location: {selected_location.city}, {selected_location.country} (ID: {selected_location.id})"
            )

            state.birth_location_id = selected_location.id
            state.birth_place = self._format_location_display_name(selected_location)
            workflow_ctx.selected_location = selected_location
            workflow_ctx.pending_location_candidates = None
            workflow_ctx.current_step = AddProfileStage.CONFIRMATION
            workflow_ctx.confirmation_prompt_shown = True

            response_text = self._format_confirmation_summary(
                state=state,
                selected_location=workflow_ctx.selected_location,
            )
            reply_options = self._get_profile_confirmation_reply_options()
            context_updates = {
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            }

        else:
            # Multiple matches - show options and move to location resolution
            logger.info(
                f"User {session.user_id} multiple matches found, requesting selection"
            )

            response_text = self._format_location_candidates(location_result)
            reply_options = None

            workflow_ctx.current_step = AddProfileStage.LOCATION_RESOLUTION
            workflow_ctx.pending_location_candidates = location_result
            context_updates = {
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            }

        response = message.create_text_response(
            content=response_text,
            metadata={"continue_multi_turn": True},
            reply_options=reply_options,
        )

        return StepResult(
            response=response, action=StepAction.REPEAT, context_updates=context_updates
        )

    async def _stage_location_resolution(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        state: ProfileState,
        workflow_ctx: ProfileWorkflowContext,
    ) -> StepResult:
        # If there are no pending candidates yet, start resolution afresh
        if not workflow_ctx.pending_location_candidates:
            if not state.birth_place:
                # Missing birth place; bounce back to basic details
                workflow_ctx.current_step = AddProfileStage.BASIC_DETAILS
                logger.info(
                    "LOCATION_RESOLUTION -> BASIC_DETAILS (missing birth_place) | user=%s",
                    session.user_id,
                )
                response = message.create_text_response(
                    content=BASIC_DETAILS_ASK_BIRTH_PLACE,
                    metadata={"continue_multi_turn": True},
                )
                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={
                        "profile_state": state.model_dump(),
                        "profile_workflow": workflow_ctx.model_dump(),
                    },
                )

            return self._start_location_resolution(
                birth_place=state.birth_place,
                state=state,
                workflow_ctx=workflow_ctx,
                session=session,
                message=message,
            )

        # We have candidates, interpret user's selection with LLM
        candidates = workflow_ctx.pending_location_candidates
        assert candidates is not None
        logger.debug(
            "LOCATION_RESOLUTION step | user=%s | search_term=%s | exact=%s fuzzy=%s",
            session.user_id,
            candidates.search_term,
            len(candidates.exact_matches),
            len(candidates.fuzzy_matches),
        )
        llm_response = await self._get_location_resolution_llm_response(
            candidates=candidates, message=message, session=session
        )
        if (
            llm_response.response_type == LLMResponseType.ERROR
            or not llm_response.object
        ):
            logger.error(
                "LLM(LOCATION_RESOLUTION) error | user=%s | response_type=%s",
                session.user_id,
                llm_response.response_type,
            )
            return self._create_error_result(message, ERROR_LLM_PROCESSING_RETRY)

        llm_obj: LocationResolutionLLMResponse = llm_response.object  # type: ignore[assignment]
        logger.debug(
            "LOCATION_RESOLUTION LLM extracted | user=%s | selected_location_id=%s | response_len=%s",
            session.user_id,
            llm_obj.selected_location_id,
            len(llm_obj.response_text) if llm_obj.response_text else 0,
        )

        if llm_obj.selected_location_id is not None:
            selected = self._find_location_by_id(
                candidates, llm_obj.selected_location_id
            )
            if selected is not None:
                logger.info(
                    f"User {session.user_id} selected location: {selected.city}, {selected.country} (ID: {selected.id})"
                )
                state.birth_location_id = selected.id
                selected_location: LocationCandidate = selected
                state.birth_place = self._format_location_display_name(
                    selected_location
                )
                workflow_ctx.selected_location = selected_location
                workflow_ctx.pending_location_candidates = None
                workflow_ctx.current_step = AddProfileStage.CONFIRMATION
                workflow_ctx.confirmation_prompt_shown = True

                confirmation_text = self._format_confirmation_summary(
                    state=state, selected_location=workflow_ctx.selected_location
                )
                response = message.create_text_response(
                    content=confirmation_text,
                    metadata={"continue_multi_turn": True},
                    reply_options=self._get_profile_confirmation_reply_options(),
                )
                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={
                        "profile_state": state.model_dump(),
                        "profile_workflow": workflow_ctx.model_dump(),
                    },
                )

        # No valid selection yet; continue the conversation
        logger.debug(
            "LOCATION_RESOLUTION continue | user=%s | echo_options=%s",
            session.user_id,
            not bool(llm_obj.response_text),
        )
        response_text = (
            llm_obj.response_text
            if llm_obj.response_text
            else self._format_location_candidates(candidates)
        )
        response = message.create_text_response(
            content=response_text,
            metadata={"continue_multi_turn": True},
        )
        return StepResult(
            response=response,
            action=StepAction.REPEAT,
            context_updates={
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            },
        )

    async def _stage_confirmation(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        state: ProfileState,
        workflow_ctx: ProfileWorkflowContext,
    ) -> StepResult:
        logger.debug(
            "CONFIRMATION | user=%s | current_state: name=%s date=%s time=%s place=%s gender=%s relationship=%s",
            session.user_id,
            state.name,
            state.birth_date,
            state.birth_time,
            state.birth_place,
            getattr(state.gender, "value", None) if state.gender else None,
            getattr(state.relationship, "value", None) if state.relationship else None,
        )
        llm_response = await self._get_confirmation_llm_response(
            state=state, message=message, session=session
        )
        if (
            llm_response.response_type == LLMResponseType.ERROR
            or not llm_response.object
        ):
            logger.error(
                "LLM(CONFIRMATION) error | user=%s | response_type=%s",
                session.user_id,
                llm_response.response_type,
            )
            return self._create_error_result(message, ERROR_LLM_PROCESSING_RETRY)

        llm_obj: ConfirmationLLMResponse = llm_response.object  # type: ignore[assignment]
        logger.debug(
            "CONFIRMATION LLM extracted | user=%s | confirmed=%s | has_edits=%s",
            session.user_id,
            llm_obj.confirmed,
            bool(llm_obj.edits),
        )

        # Apply edits if any
        if llm_obj.edits:
            edits = llm_obj.edits
            logger.info(
                "CONFIRMATION apply edits | user=%s | name=%s date=%s time=%s place=%s gender=%s relationship=%s",
                session.user_id,
                edits.name,
                edits.birth_date,
                edits.birth_time,
                edits.birth_place,
                getattr(edits.gender, "value", None) if edits.gender else None,
                (
                    getattr(edits.relationship, "value", None)
                    if edits.relationship
                    else None
                ),
            )
            if edits.name is not None:
                state.name = edits.name
            if edits.birth_date is not None:
                state.birth_date = edits.birth_date
            if edits.birth_time is not None:
                state.birth_time = edits.birth_time
            if edits.birth_place is not None:
                # If birth place provided in edits, always reset and re-resolve
                if state.birth_place != edits.birth_place:
                    logger.info(
                        "CONFIRMATION | user=%s | birth_place changed '%s' -> '%s' | resetting birth_location_id",
                        session.user_id,
                        state.birth_place,
                        edits.birth_place,
                    )
                state.birth_location_id = None
                state.birth_place = edits.birth_place
            if edits.gender is not None:
                state.gender = edits.gender
            if edits.relationship is not None:
                state.relationship = edits.relationship

            # Determine next step after edits
            # Reset confirmation prompt flag since details changed
            workflow_ctx.confirmation_prompt_shown = False
            basic_fields_changed = any(
                [
                    edits.name is not None,
                    edits.birth_date is not None,
                    edits.birth_time is not None,
                    edits.gender is not None,
                    edits.relationship is not None,
                ]
            )
            birth_place_changed = edits.birth_place is not None

            if birth_place_changed and basic_fields_changed:
                # Case 3: both birthplace and other fields changed → go to BASIC_DETAILS cleanly
                workflow_ctx.current_step = AddProfileStage.BASIC_DETAILS
                workflow_ctx.confirmation_prompt_shown = False
                logger.info(
                    "Transition -> BASIC_DETAILS (edits include birth_place and other fields) | user=%s",
                    session.user_id,
                )
                content_text = (
                    llm_obj.response_text or BASIC_DETAILS_UPDATE_CONFIRMATION
                )
                reply_options = (
                    self._get_basic_details_update_reply_options()
                    if content_text == BASIC_DETAILS_UPDATE_CONFIRMATION
                    else None
                )
                response = message.create_text_response(
                    content=content_text,
                    metadata={"continue_multi_turn": True},
                    reply_options=reply_options,
                )
                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={
                        "profile_state": state.model_dump(),
                        "profile_workflow": workflow_ctx.model_dump(),
                    },
                )

            if birth_place_changed and state.birth_place:
                # Case 2 (with value provided): birth place changed only → immediately start resolution
                logger.info(
                    "Transition -> LOCATION_RESOLUTION (after birth_place edit) | user=%s | birth_place=%s",
                    session.user_id,
                    state.birth_place,
                )
                workflow_ctx.confirmation_prompt_shown = False
                return self._start_location_resolution(
                    birth_place=state.birth_place,
                    state=state,
                    workflow_ctx=workflow_ctx,
                    session=session,
                    message=message,
                )

            if llm_obj.wants_birth_place_change and not state.birth_place:
                # Case 2 (without value): ask user for birth place
                workflow_ctx.current_step = AddProfileStage.BASIC_DETAILS
                workflow_ctx.confirmation_prompt_shown = False
                logger.info(
                    "Transition -> BASIC_DETAILS (ask for birth_place after change request) | user=%s",
                    session.user_id,
                )
                response = message.create_text_response(
                    content=BASIC_DETAILS_ASK_BIRTH_PLACE,
                    metadata={"continue_multi_turn": True},
                )
                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={
                        "profile_state": state.model_dump(),
                        "profile_workflow": workflow_ctx.model_dump(),
                    },
                )

            # Case 1 or no relevant changes: re-show updated confirmation summary
            logger.info(
                "CONFIRMATION re-show summary (post-edits) | user=%s",
                session.user_id,
            )
            workflow_ctx.confirmation_prompt_shown = False
            summary_text = self._format_confirmation_summary(
                state=state, selected_location=workflow_ctx.selected_location
            )
            response = message.create_text_response(
                content=summary_text,
                metadata={"continue_multi_turn": True},
                reply_options=self._get_profile_confirmation_reply_options(),
            )
            return StepResult(
                response=response,
                action=StepAction.REPEAT,
                context_updates={
                    "profile_state": state.model_dump(),
                    "profile_workflow": workflow_ctx.model_dump(),
                },
            )

        # If user confirmed, create profile
        if llm_obj.confirmed is True:
            logger.info("CONFIRMATION confirmed | user=%s", session.user_id)
            return await self._handle_profile_creation(
                updated_state=state,
                session=session,
                message=message,
            )

        # Otherwise, show confirmation summary again or assistant's reply
        if not llm_obj.response_text:
            if not workflow_ctx.confirmation_prompt_shown:
                confirmation_text = self._format_confirmation_summary(
                    state=state, selected_location=workflow_ctx.selected_location
                )
                reply_options = self._get_profile_confirmation_reply_options()
                workflow_ctx.confirmation_prompt_shown = True
            else:
                confirmation_text = PROFILE_CONFIRMATION_NUDGE
                reply_options = self._get_profile_confirmation_reply_options()
        else:
            confirmation_text = llm_obj.response_text
            reply_options = None

        response = message.create_text_response(
            content=confirmation_text,
            metadata={"continue_multi_turn": True},
            reply_options=reply_options,
        )
        return StepResult(
            response=response,
            action=StepAction.REPEAT,
            context_updates={
                "profile_state": state.model_dump(),
                "profile_workflow": workflow_ctx.model_dump(),
            },
        )

    async def _handle_profile_creation(
        self,
        updated_state: ProfileState,
        session: Session,
        message: CanonicalRequestMessage,
    ) -> StepResult:
        logger.info(
            f"User {session.user_id} creating profile for {updated_state.name} born in {updated_state.birth_place}"
        )

        # Calculate sun sign if possible
        sun_sign = None
        if updated_state.birth_datetime:
            sun_sign = get_sun_sign(updated_state.birth_datetime.date())
            logger.debug(
                f"User {session.user_id} calculated sun sign: {sun_sign} from birth date {updated_state.birth_datetime.date()}"
            )
        else:
            logger.warning(
                f"User {session.user_id} missing birth datetime for sun sign calculation"
            )

        # Get location timezone and convert birth_datetime from local time to UTC
        birth_datetime_utc = self._convert_birth_datetime_to_utc(
            updated_state.birth_datetime, updated_state.birth_location_id
        )

        profile = self.profiles_dao.create_profile(
            user_id=session.user_id,
            name=updated_state.name,
            birth_datetime=birth_datetime_utc,
            birth_place=updated_state.birth_place,
            birth_location_id=updated_state.birth_location_id,
            gender=updated_state.gender,
            sun_sign=sun_sign,
            relationship=updated_state.relationship,
        )
        logger.info(
            "Profile created | user=%s | profile_id=%s | name=%s | sun_sign=%s",
            session.user_id,
            profile.profile_id,
            profile.name,
            getattr(profile.sun_sign, "value", None) if profile.sun_sign else None,
        )

        # Update session with current profile details
        session.current_profile_id = profile.profile_id
        session.session_metadata["current_profile"] = {
            "profile_id": str(profile.profile_id),
            "name": profile.name,
            "birth_datetime": (
                profile.birth_datetime.isoformat() if profile.birth_datetime else None
            ),
            "birth_place": profile.birth_place,
            "gender": profile.gender.value if profile.gender else None,
            "sun_sign": profile.sun_sign.value if profile.sun_sign else None,
        }

        # Create personalized success message using profile name
        profile_name = profile.name or "the profile"
        response_text = PROFILE_CREATION_SUCCESS_TEMPLATE.format(
            profile_name=profile_name
        )
        response = message.create_text_response(
            content=response_text,
            metadata={"continue_multi_turn": False},
            reply_options=self._get_profile_creation_success_reply_options(),
        )

        return StepResult(
            response=response,
            action=StepAction.CONTINUE,
            context_updates={
                "profile_state": updated_state.model_dump(),
                "profile_id": str(profile.profile_id),
                "profile_created": True,
            },
        )

    def _resolve_birth_location(self, birth_place: str) -> LocationSearchResult:
        """Local-only implementation of birth location resolution (same as handler)."""
        logger.debug(f"Resolving birth location: {birth_place}")

        geolocation_service = GeolocationService()
        result = geolocation_service.search_location(birth_place)

        if result.total_results > 0:
            return result

        return LocationSearchResult(
            exact_matches=[],
            fuzzy_matches=[],
            search_term=birth_place,
            total_results=0,
        )

    def _format_location_display_name(self, location: LocationCandidate) -> str:
        display_name = location.city
        if location.province:
            display_name += f", {location.province}"
        if location.country:
            display_name += f", {location.country}"
        return display_name

    def _format_location_candidates(self, location_result: LocationSearchResult) -> str:
        if location_result.total_results == 0:
            return LOCATION_NO_MATCHES.format(search_term=location_result.search_term)

        exact_matches_section = ""
        fuzzy_matches_section = ""
        option_number = 1

        if location_result.exact_matches:
            exact_matches_section = f"I found {len(location_result.exact_matches)} exact match(es) for '{location_result.search_term}':\n"
            for location in location_result.exact_matches:
                location_display = self._format_location_display_name(location)
                exact_matches_section += f"{option_number}. {location_display}\n"
                option_number += 1

        if location_result.fuzzy_matches:
            if location_result.exact_matches:
                fuzzy_matches_section += "\n"
            fuzzy_matches_section += f"I also found {len(location_result.fuzzy_matches)} similar location(s):\n"
            for location, score in location_result.fuzzy_matches:
                location_display = self._format_location_display_name(location)
                fuzzy_matches_section += f"{option_number}. {location_display}\n"
                option_number += 1

        return LOCATION_CANDIDATES_TEMPLATE.format(
            exact_matches_section=exact_matches_section,
            fuzzy_matches_section=fuzzy_matches_section,
        )

    def _format_location_candidates_for_llm(
        self, location_result: LocationSearchResult
    ) -> str:
        user_display = self._format_location_candidates(location_result)

        llm_context = "\n\nLocation ID Mapping for Selection:\n"
        option_number = 1

        for location in location_result.exact_matches:
            location_display = self._format_location_display_name(location)
            llm_context += (
                f"Option {option_number}: {location_display} → ID {location.id}\n"
            )
            option_number += 1

        for location, score in location_result.fuzzy_matches:
            location_display = self._format_location_display_name(location)
            llm_context += (
                f"Option {option_number}: {location_display} → ID {location.id}\n"
            )
            option_number += 1

        return user_display + llm_context

    def _find_location_by_id(
        self, location_result: LocationSearchResult, location_id: int
    ) -> Optional[LocationCandidate]:
        for location in location_result.exact_matches:
            if location.id == location_id:
                return location
        for location, _ in location_result.fuzzy_matches:
            if location.id == location_id:
                return location
        available_ids = [loc.id for loc in location_result.exact_matches] + [
            loc.id for loc, _ in location_result.fuzzy_matches
        ]
        logger.warning(
            f"Location ID {location_id} not found in search results (available: {available_ids})"
        )
        return None

    def _format_confirmation_summary(
        self, state: ProfileState, selected_location: Optional[LocationCandidate]
    ) -> str:
        # Prepare timezone info if available
        timezone_info = ""
        if selected_location and selected_location.timezone:
            timezone_info = f" (Timezone: {selected_location.timezone})"

        return PROFILE_CONFIRMATION_TEMPLATE.format(
            name=state.name,
            birth_date=(
                state.birth_date.strftime("%B %d, %Y")
                if state.birth_date
                else PROFILE_NOT_SET_VALUE
            ),
            birth_time=(
                state.birth_time.strftime("%I:%M %p")
                if state.birth_time
                else PROFILE_NOT_SET_VALUE
            ),
            birth_place=state.birth_place,
            timezone_info=timezone_info,
            gender=state.gender.value if state.gender else PROFILE_NOT_SET_VALUE,
            relationship=(
                state.relationship.value
                if state.relationship
                else PROFILE_NOT_SET_VALUE
            ),
        )

    def _create_error_result(
        self, message: CanonicalRequestMessage, error_msg: str
    ) -> StepResult:
        response = message.create_error_response(
            error_message=ERROR_GENERAL,
            metadata={"error": error_msg},
        )
        return StepResult(response=response, action=StepAction.REPEAT)
