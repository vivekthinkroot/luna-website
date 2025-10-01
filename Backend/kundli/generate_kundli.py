"""
Native workflow steps for kundli generation.

These steps implement kundli generation logic natively within the workflow system,
providing better conversation flow and preparation for future enhancements.
"""

import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from config.settings import get_kundli_settings
from dao.profiles import Profile, ProfileDAO
from kundli.artifact_builder import get_kundli_artifacts
from kundli.astro_profile import BasicKundliInfo, build_and_store_astro_profile_data
from kundli.utils import get_sun_sign_description
from llms.client import LLMClient, LLMResponseType
from llms.models import LLMMessage, LLMMessageRole
from services.channels import ChannelsService
from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps, Workflows
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, ContentType, QuickReplyOption
from utils.sessions import Session

logger = get_logger()


class KundliConversationState(BaseModel):
    """State tracking for kundli generation conversation."""

    conversation_started: bool = False
    sun_sign_shown: bool = False
    user_wants_detailed: Optional[bool] = None
    detailed_kundli_requested: bool = False
    conversation_complete: bool = False


class KundliResponseClassification(BaseModel):
    """Classification of user's response in kundli conversation."""

    response_type: str  # wants_detailed_kundli, declines_detailed_kundli, astrology_question, other_topic
    response_text: str
    confidence: float = 0.8
    wants_detailed: Optional[bool] = None


KUNDLI_CLASSIFICATION_PROMPT = """
You are an AI assistant that classifies user responses in a Vedic astrology context.

The user has been shown their sun sign description and asked if they want a detailed kundli analysis.

Classify the user's response into one of these categories:
1. "wants_detailed_kundli" - User clearly says yes, wants, needs, or requests detailed kundli/astrology reading
2. "declines_detailed_kundli" - User clearly says no, declines, or indicates they don't want detailed analysis
3. "astrology_question" - User asks about astrology, planets, zodiac, horoscope, or other astrological topics
4. "other_topic" - User talks about something completely unrelated to astrology

User's response: {user_message}

Based on the classification, provide:
- response_type: One of the four categories above
- response_text: A polite, appropriate response based on the classification
- confidence: Your confidence in the classification (0.0 to 1.0)
- wants_detailed: true if wants detailed kundli, false if declines, null otherwise
"""

# Response constants for user-facing messages
DETAILED_KUNDLI_OFFER = "Would you like me to generate a detailed Vedic natal chart (Kundli) and analysis for you?"

DETAILED_KUNDLI_ACCEPTED_RESPONSE = (
    "Perfect! I'll generate your detailed Vedic natal chart (Kundli) now. "
    "This involves complex astrological calculations and will take a few minutes.\n\n"
    "Please wait while I prepare your comprehensive kundli report..."
)

DETAILED_KUNDLI_DECLINED_RESPONSE = (
    "Sure! Feel free to reach out anytime if you'd like to chat more about "
    "Vedic astrology or want a detailed kundli reading. I'm here to "
    "help you explore the fascinating world of Vedic astrology whenever you're ready."
)

ASTROLOGY_QUESTION_REDIRECT_RESPONSE = (
    "I understand you're interested in deeper astrological insights. "
    "All detailed analysis, including planetary positions, yogas, and life path "
    "guidance, etc. requires a comprehensive Vedic natal chart (Kundli).\n\n"
    "Would you like to generate a detailed kundli analysis for you?"
)

OFF_TOPIC_REDIRECT_RESPONSE = (
    "I'm focused on helping you with Vedic astrology and kundli analysis. "
    "I can provide insights about your sun sign, generate detailed natal charts, "
    "and offer comprehensive astrological readings.\n\n"
    "Would you like to explore your astrological profile or get a detailed kundli analysis?"
)

CLASSIFICATION_ERROR_FALLBACK_RESPONSE = (
    "I can help you with Vedic astrology, and kundli analysis.\n\n"
    "Would you like to know more about your sun sign, "
    "or get a detailed natal chart reading?"
)

NO_PROFILE_RESPONSE = (
    "I need the person's profile to generate a kundli. Let's do that first.\n\n"
    "\n\nPlease share the person's:\n- Name\n- Date of Birth\n- Time of Birth\n- Place of Birth\n- Gender\n- Relationship to you"
)

INVALID_PROFILE_RESPONSE = (
    "Let's get the birth details about this person first.\n"
    "\n\nPlease share the person's:\n- Name\n- Date of Birth\n- Time of Birth\n- Place of Birth\n- Gender\n- Relationship to you"
)

ERROR_RESPONSE_GENERAL = "Oops, something went wrong. Please try again."

KUNDLI_DOCUMENT_RESPONSE = (
    "🎉 Your personalized Vedic Kundli is ready, {user_name}! 🎉\n\n"
    "✨ This comprehensive astrological report includes:\n"
    "• Your birth chart (Janma Kundli)\n"
    "• Planetary positions and their influences\n"
    "• Astrological houses and their significance\n"
    "• Life path guidance and predictions\n\n"
    "✨ May the stars guide you on your journey!"
)

QNA_NUDGE_TEXT = (
    "You can now get detailed vedic astrology based insights for this kundli. \n\n"
    "You can ask about career, health, relationships, finance, travel, or anything else."
)

BASIC_ASTRO_RESPONSE_TEMPLATE = (
    "🎉 Your Vedic Kundli is ready!!\n\n"
    "🌟 Key Astrological Details:\n"
    "*Name:* {user_name}\n"
    "*Birth Nakshatra:* {birth_star}\n"
    "*Moon Sign (Rashi):* {moon_sign}\n"
    "*Lagna:* {lagna}\n"
    "*Current Maha Dasha:* {maha_dasha_planet}\n"
    "{maha_dasha_period_text}"
    "\n🔮 This forms the foundation of your Vedic natal chart. Your astrological profile has been stored for analysis & deeper insights.\n\n"
    "✨ May the stars guide you on your journey! ✨"
)


class GenerateKundliStep(WorkflowStep):
    """
    Native workflow step for kundli generation conversation.

    This step manages the kundli generation flow, from showing sun sign
    to handling user's decision about detailed analysis.
    """

    def __init__(self):
        super().__init__(Steps.KUNDLI_GENERATION.value)
        self.llm_client = LLMClient()
        self.profiles_dao = ProfileDAO()
        # This will be populated from workflow_context when execute is called
        self.workflow_id: str = "generate_kundli"

    def _get_kundli_yes_no_reply_options(self) -> List[QuickReplyOption]:
        """Get kundli yes/no quick reply options using current workflow ID."""
        return [
            QuickReplyOption.build(
                self.workflow_id, "kundli_yes", "Yes, Generate Kundli"
            ),
            QuickReplyOption.build(self.workflow_id, "kundli_no", "No, maybe later"),
        ]

    def _get_kundli_explore_reply_options(self) -> List[QuickReplyOption]:
        """Get kundli explore quick reply options using current workflow ID."""
        return [
            QuickReplyOption.build(
                self.workflow_id, "detailed_kundli", "Detailed kundli"
            ),
            QuickReplyOption.build(
                self.workflow_id, "sun_sign_info", "About my sun sign"
            ),
        ]

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """Execute kundli generation step."""
        try:
            # Extract the current workflow ID from the workflow context
            # This is the actual workflow (e.g., "add_profile", "generate_kundli")
            self.workflow_id = workflow_id

            # Check if user has a profile
            profile_id = session.current_profile_id
            if not profile_id:
                return self._create_no_profile_result(message)

            # Get profile from database
            profile: Profile | None = self.profiles_dao.get_profile_by_id(
                str(profile_id)
            )
            if not profile or not profile.sun_sign:
                return self._create_invalid_profile_result(message)

            # Get conversation state from workflow context
            state_dict = workflow_context.get("kundli_state", {})
            conversation_state = KundliConversationState(**state_dict)

            if not conversation_state.conversation_started:
                # First interaction - show sun sign description
                return await self._handle_initial_interaction(
                    message, profile, conversation_state, workflow_context
                )
            else:
                # User has responded to sun sign - classify their response
                return await self._handle_user_response(
                    message, profile, conversation_state, workflow_context
                )

        except Exception as e:
            logger.exception(f"Error in GenerateKundliStep: {e}")
            return self._create_error_result(
                message, "Something went wrong with kundli generation"
            )

    async def _handle_initial_interaction(
        self,
        message: CanonicalRequestMessage,
        profile,
        conversation_state: KundliConversationState,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """Handle the first interaction - show sun sign and ask about detailed kundli."""

        # Get sun sign description
        sun_sign_description = get_sun_sign_description(profile.sun_sign)
        sun_sign_description += "\n\n" + DETAILED_KUNDLI_OFFER

        # Update conversation state
        conversation_state.conversation_started = True
        conversation_state.sun_sign_shown = True

        response = message.create_text_response(
            content=sun_sign_description,
            metadata={"continue_multi_turn": True},
            reply_options=self._get_kundli_yes_no_reply_options(),
        )

        return StepResult(
            response=response,
            action=StepAction.REPEAT,
            context_updates={
                "kundli_state": conversation_state.model_dump(),
                "profile_id": str(profile.profile_id),
                "sun_sign": profile.sun_sign.value,
            },
        )

    async def _handle_user_response(
        self,
        message: CanonicalRequestMessage,
        profile: Profile,
        conversation_state: KundliConversationState,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """Handle user's response to the sun sign description."""

        # Classify user's response using LLM
        classification = await self._classify_user_response(message.content)

        if classification.response_type == "wants_detailed_kundli":
            # User wants detailed kundli - generate it
            conversation_state.user_wants_detailed = True
            conversation_state.detailed_kundli_requested = True
            conversation_state.conversation_complete = True

            # First, send the "generating" message
            initial_response = message.create_text_response(
                content=DETAILED_KUNDLI_ACCEPTED_RESPONSE,
                metadata={"continue_multi_turn": False},
            )

            # Generate the kundli artifacts asynchronously
            asyncio.create_task(self.generate_and_send_kundli(message, profile))

            return StepResult(
                response=initial_response,
                action=StepAction.COMPLETE,
                context_updates={
                    "kundli_state": conversation_state.model_dump(),
                    "wants_detailed_kundli": True,
                    "kundli_interaction_complete": True,
                },
            )

        elif classification.response_type == "declines_detailed_kundli":
            # User declines detailed kundli
            conversation_state.user_wants_detailed = False
            conversation_state.conversation_complete = True

            response_text = DETAILED_KUNDLI_DECLINED_RESPONSE

            response = message.create_text_response(
                content=response_text, metadata={"continue_multi_turn": False}
            )

            return StepResult(
                response=response,
                action=StepAction.COMPLETE,
                context_updates={
                    "kundli_state": conversation_state.model_dump(),
                    "wants_detailed_kundli": False,
                },
            )

        elif classification.response_type == "astrology_question":
            # User asks astrology question - redirect to detailed kundli
            response_text = ASTROLOGY_QUESTION_REDIRECT_RESPONSE

            response = message.create_text_response(
                content=response_text,
                metadata={"continue_multi_turn": True},
                reply_options=self._get_kundli_yes_no_reply_options(),
            )

            return StepResult(
                response=response,
                action=StepAction.REPEAT,
                context_updates={
                    "kundli_state": conversation_state.model_dump(),
                },
            )

        else:  # other_topic
            # User talks about something else - redirect to app focus
            response_text = OFF_TOPIC_REDIRECT_RESPONSE

            response = message.create_text_response(
                content=response_text,
                metadata={"continue_multi_turn": True},
                reply_options=self._get_kundli_explore_reply_options(),
            )

            return StepResult(
                response=response,
                action=StepAction.REPEAT,
                context_updates={
                    "kundli_state": conversation_state.model_dump(),
                },
            )

    async def _send_basic_astro_response(
        self,
        message: CanonicalRequestMessage,
        profile: Profile,
        basic_astro_data: BasicKundliInfo
    ):
        """Send a simple text response with basic astro information."""
        try:
            # Format the basic astro data using the template
            user_name = profile.name or "User"

            # Prepare dasha period text
            maha_dasha_period_text = f"📅 *Current Maha Dasha Period:* {basic_astro_data.current_maha_dasha_start_date} to {basic_astro_data.current_maha_dasha_end_date}\n" if basic_astro_data.current_maha_dasha_start_date and basic_astro_data.current_maha_dasha_end_date else ""

            response_text = BASIC_ASTRO_RESPONSE_TEMPLATE.format(
                user_name=user_name.title(),
                birth_star=basic_astro_data.birth_star,
                moon_sign=basic_astro_data.moon_sign,
                lagna=basic_astro_data.lagna,
                maha_dasha_planet=basic_astro_data.current_maha_dasha_planet,
                maha_dasha_period_text=maha_dasha_period_text,
            )

            basic_response = message.create_text_response(
                content=response_text,
                metadata={
                    "kundli_generated": True,
                    "profile_id": str(profile.profile_id),
                    "basic_astro_response": True,
                },
            )

            channels_service = ChannelsService()
            await channels_service.send_message(message.user_id, basic_response)  # type: ignore

            logger.info(
                f"Basic astro response sent successfully to user {message.user_id} for profile {profile.profile_id}"
            )

        except Exception as e:
            logger.warning(
                f"Exception - failed to send basic astro response to user {message.user_id}: {e}"
            )
            # Don't raise the exception - let the Q&A nudge still be sent


    async def generate_and_send_kundli(
        self, message: CanonicalRequestMessage, profile: Profile
    ):
        """Generate kundli artifacts and send them to the user."""
        try:
            profile_id = str(profile.profile_id)
            logger.info(f"Starting kundli generation for profile {profile_id}")
            channels_service = ChannelsService()

            # Step 1: Generate and store astro profile data
            basic_astro_data: BasicKundliInfo = await build_and_store_astro_profile_data(profile_id)
            logger.info(
                f"Astro profile data generated and stored for profile {profile_id}"
            )

            # Step 2: Check if PDF needs to be sent to user (based on settings)
            kundli_settings = get_kundli_settings()
            if kundli_settings.send_pdf_to_user:
                # Get artifacts and send PDF
                artifacts = await get_kundli_artifacts(profile_id)

                if not artifacts.is_success:
                    logger.error(
                        f"Failed to generate artifacts for profile {profile_id}: {artifacts.error_message}"
                    )
                    # Send error message to user
                    error_response = message.create_text_response(
                        content="I apologize, but there was an error generating your kundli report. Please try again later.",
                        metadata={
                            "error": "artifact_generation_failed",
                            "profile_id": profile_id,
                        },
                    )

                    try:
                        channels_service = ChannelsService()
                        await channels_service.send_message(message.user_id, error_response)  # type: ignore
                    except Exception as send_error:
                        logger.exception(
                            f"Failed to send error message to user: {send_error}"
                        )
                    return

                logger.info(
                    f"Kundli artifacts generated successfully for profile {profile_id}"
                )

                # Prepare document response
                user_name = profile.name or "User"
                response_text = KUNDLI_DOCUMENT_RESPONSE.format(
                    user_name=user_name.title()
                )

                # Send PDF if available
                if artifacts.pdf and len(artifacts.pdf) > 0:
                    filename = f"{user_name.title()} - Luna Report.pdf"
                    mime_type = "application/pdf"
                    binary_content = artifacts.pdf
                    logger.info(
                        f"Preparing PDF kundli document for profile {profile_id}"
                    )

                    kundli_document_response = message.create_response(
                        content=response_text,
                        content_type=ContentType.DOCUMENT,
                        metadata={
                            "filename": filename,
                            "mime_type": mime_type,
                            "kundli_generated": True,
                            "profile_id": profile_id,
                        },
                        binary_content=binary_content,
                    )

                    # Send the document response
                    await channels_service.send_message(
                        message.user_id, kundli_document_response  # type: ignore
                    )

                    logger.info(
                        f"Kundli document sent successfully to user {message.user_id}"
                    )
                else:
                    logger.info(f"PDF not available for profile {profile_id}")
            else:
                logger.info("PDF sending disabled system-wide")
                # Send a simple text response with basic astro information
                await self._send_basic_astro_response(message, profile, basic_astro_data)

            
            # After processing, schedule a gentle nudge to start Q&A
            # Even if the document is not sent, the astro profile is generated, so we still want to send the nudge
            async def _send_qna_nudge():
                try:
                    await asyncio.sleep(5)

                    nudge_reply_options = [
                        QuickReplyOption.build(
                            Workflows.PROFILE_QNA.value, "start", "Ask a question now"
                        ),
                        QuickReplyOption.build(
                            Workflows.MAIN_MENU.value, "open", "Main menu"
                        ),
                    ]

                    nudge_response = message.create_text_response(
                        content=QNA_NUDGE_TEXT,
                        metadata={
                            "continue_multi_turn": True,
                            "profile_id": profile_id,
                            "nudged_for_qna": True,
                        },
                        reply_options=nudge_reply_options,
                    )

                    await channels_service.send_message(
                        message.user_id, nudge_response  # type: ignore
                    )
                    logger.info(
                        f"Sent post-kundli QnA nudge to user {message.user_id} for profile {profile_id}"
                    )
                except Exception as nudge_err:
                    logger.warning(
                        f"Failed to send QnA nudge to user {message.user_id}: {nudge_err}"
                    )

            asyncio.create_task(_send_qna_nudge())

        except Exception as e:
            logger.exception(
                f"Error generating or sending kundli for profile {profile_id}: {e}"
            )

            # Send error message to user
            error_response = message.create_text_response(
                content="I apologize, but there was an error generating your kundli report. Please try again later.",
                metadata={
                    "error": "kundli_generation_failed",
                    "profile_id": profile_id,
                },
            )

            try:
                channels_service = ChannelsService()

                await channels_service.send_message(
                    message.user_id, error_response  # type: ignore
                )
            except Exception as send_error:
                logger.exception(f"Failed to send error message to user: {send_error}")

    async def _classify_user_response(
        self, user_message: str
    ) -> KundliResponseClassification:
        """Classify user's response to determine next action."""

        system_prompt = KUNDLI_CLASSIFICATION_PROMPT.format(user_message=user_message)

        llm_response = await self.llm_client.get_response(
            messages=[
                LLMMessage(role=LLMMessageRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMMessageRole.USER, content=user_message),
            ],
            temperature=0.3,
            auto=True,
            response_model=KundliResponseClassification,
            
        )

        if llm_response.response_type == LLMResponseType.ERROR:
            # Default to other topic if classification fails
            return KundliResponseClassification(
                response_type="other_topic",
                response_text=CLASSIFICATION_ERROR_FALLBACK_RESPONSE,
                confidence=0.5,
            )

        if isinstance(llm_response.object, KundliResponseClassification):
            return llm_response.object
        else:
            # Fallback if object is not the expected type
            return KundliResponseClassification(
                response_type="other_topic",
                response_text=CLASSIFICATION_ERROR_FALLBACK_RESPONSE,
                confidence=0.5,
            )

    def _create_no_profile_result(self, message: CanonicalRequestMessage) -> StepResult:
        """Create result when user has no profile."""
        response = message.create_text_response(
            content=NO_PROFILE_RESPONSE,
            metadata={"continue_multi_turn": False},
        )

        # Jump to profile resolution step first
        return StepResult(
            response=response,
            action=StepAction.JUMP,
            next_step_id=Steps.PROFILE_RESOLUTION.value,
        )

    def _create_invalid_profile_result(
        self, message: CanonicalRequestMessage
    ) -> StepResult:
        """Create result when profile is invalid or incomplete."""
        response = message.create_text_response(
            content=INVALID_PROFILE_RESPONSE,
            metadata={"error": "incomplete_profile"},
        )

        # Ask user to resolve or update profile via profile resolution
        return StepResult(
            response=response,
            action=StepAction.JUMP,
            next_step_id=Steps.PROFILE_RESOLUTION.value,
        )

    def _create_error_result(
        self, message: CanonicalRequestMessage, error_msg: str
    ) -> StepResult:
        """Create error result for failed operations."""
        response = message.create_error_response(
            error_message=ERROR_RESPONSE_GENERAL,
            metadata={"error": error_msg},
        )

        return StepResult(response=response, action=StepAction.REPEAT)
