"""
System Prompt Service for Profile Q&A

This service constructs detailed system prompts containing the user's astrology profile information
for LLM interactions in the Q&A workflow using either a simple template or Jinja2 templates.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, Template

from dao.profiles import ProfileDAO, ProfileData
from kundli.divineapi_v2.api_response_models import (
    PlanetaryPositionsResponse, PlanetModel, PlanetName, ZodiacSign)
from kundli.divineapi_v2.output_model import RawAstroAPIData
from utils.logger import get_logger

from .astro_utils import AstroUtilsService

logger = get_logger()

# Configuration flag for backward compatibility
USE_JINJA_TEMPLATE = True


class SystemPromptService:
    """Service for constructing detailed system prompts with astrology profile data using either simple or Jinja2 templates."""

    def __init__(self):
        self.profile_dao = ProfileDAO()
        self.jinja_env = self._setup_jinja_environment() if USE_JINJA_TEMPLATE else None
        self.astro_utils = AstroUtilsService()

    def _setup_jinja_environment(self) -> Environment:
        """Set up Jinja2 environment with custom filters and globals."""
        # Get the directory containing this file
        template_dir = os.path.dirname(os.path.abspath(__file__))

        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # We don't need HTML escaping for system prompts
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        env.filters["default"] = self._default_filter
        env.filters["first"] = self._first_filter
        env.filters["format_date"] = self._format_date_filter

        # Add custom globals
        env.globals["format_date"] = self._format_date_global

        return env

    def _default_filter(self, value: Any, default_value: str = "Not specified") -> str:
        """Custom filter to provide default values for None/empty values."""
        if value is None or value == "":
            return default_value
        return str(value)

    def _first_filter(self, value: Any) -> Any:
        """Custom filter to get the first item from a list or dict."""
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        elif isinstance(value, dict) and len(value) > 0:
            # For dict, return first key-value pair as a dict
            first_key = next(iter(value))
            return value[first_key]
        return value

    def _format_date_filter(self, value: Any, format_str: str = "dd-mmm-yyyy") -> str:
        """Custom filter to format dates."""
        if value is None:
            return "Not specified"

        try:
            if hasattr(value, "strftime"):
                if format_str == "dd-mmm-yyyy":
                    return value.strftime("%d-%b-%Y")
                elif format_str == "dd-mm-yyyy":
                    return value.strftime("%d-%m-%Y")
                else:
                    return value.strftime(format_str)
            else:
                return str(value)
        except Exception:
            return str(value)

    def _format_date_global(self, value: Any, format_str: str = "dd-mmm-yyyy") -> str:
        """Global function to format dates."""
        return self._format_date_filter(value, format_str)

    def _filter_planets(
        self, planetary_positions: PlanetaryPositionsResponse
    ) -> PlanetaryPositionsResponse:
        """Filter out outer planets (Uranus, Neptune, Pluto) from planetary positions."""
        if not planetary_positions or not planetary_positions.planets:
            return planetary_positions

        # Create a copy and filter out outer planets
        filtered_planets: list[PlanetModel] = []
        for planet in planetary_positions.planets:
            planet_name = planet.name
            if hasattr(planet_name, "value"):
                planet_name = planet_name.value  # type: ignore

            # Skip outer planets
            if planet_name not in ["Uranus", "Neptune", "Pluto"]:
                filtered_planets.append(planet)

        # Create a new PlanetaryPositionsResponse with filtered planets

        return PlanetaryPositionsResponse(
            date=planetary_positions.date,
            time=planetary_positions.time,
            planets=filtered_planets,
        )

    def construct_system_prompt(
        self, profile_id: str, current_time: Optional[datetime] = None
    ) -> str:
        """
        Construct a detailed system prompt with the user's astrology profile information.

        Args:
            profile_id: The profile ID to fetch data for
            current_time: Current time for context (defaults to UTC now)

        Returns:
            Formatted system prompt string with profile data
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        try:
            # Fetch profile data from database
            profile_data = self.profile_dao.get_profile_data(profile_id)
            if not profile_data:
                logger.warning(f"No profile data found for profile_id: {profile_id}")
                return self._get_fallback_prompt()

            if USE_JINJA_TEMPLATE:
                # Use Jinja2 template for enhanced prompts
                return self._construct_jinja_prompt(profile_data, current_time)
            else:
                # Use simple template for backward compatibility
                return self._construct_simple_prompt(profile_data, current_time)

        except Exception as e:
            logger.error(
                f"Error constructing system prompt for profile {profile_id}: {e}"
            )
            return self._get_fallback_prompt()

    def _construct_jinja_prompt(
        self, profile_data: ProfileData, current_time: datetime
    ) -> str:
        """Construct system prompt using Jinja2 template."""
        try:
            # Check if Jinja2 environment is available
            if not self.jinja_env:
                logger.warning(
                    "Jinja2 environment not available, falling back to simple template"
                )
                return self._construct_simple_prompt(profile_data, current_time)

            # Parse JSON back to RawAstroAPIData model
            raw_astro_data = RawAstroAPIData.model_validate(profile_data.kundli_data)

            # Preprocess data for the template
            filtered_planetary_positions = self._filter_planets(
                raw_astro_data.planetary_positions
            )
            navamsa_data = self.astro_utils.preprocess_navamsa_data(
                raw_astro_data.horoscope_charts
            )
            vimshottari_dasha_data = self.astro_utils.preprocess_vimshottari_dasha(
                raw_astro_data.vimshottari_dasha
            )
            processed_yogas = self.astro_utils.preprocess_yogas(raw_astro_data.yogas)

            # Calculate astro aspects and exaltation status
            astro_aspects = self.astro_utils.get_detailed_aspects_for_template(
                filtered_planetary_positions.planets
            )
            astro_exaltation = self.astro_utils.get_detailed_exaltation_for_template(
                filtered_planetary_positions.planets
            )

            # Render the Jinja2 template
            template = self.jinja_env.get_template("system_prompt_template.jinja2")

            # Prepare context data for the template
            # Note: The new BaseModel return types provide structured access to the data
            context = {
                "raw_data": raw_astro_data,
                "filtered_planetary_positions": filtered_planetary_positions,
                "navamsa_data": navamsa_data.houses,  # Access the houses dict from DivisionalChartData
                "vimshottari_dasha_data": {
                    "current_maha_dasha": (
                        vimshottari_dasha_data.current_maha_dasha.model_dump()
                        if vimshottari_dasha_data.current_maha_dasha
                        else None
                    ),
                    "current_antar_dasha": (
                        vimshottari_dasha_data.current_antar_dasha.model_dump()
                        if vimshottari_dasha_data.current_antar_dasha
                        else None
                    ),
                    "future_antar_dashas": [
                        dasha.model_dump()
                        for dasha in vimshottari_dasha_data.future_antar_dashas
                    ],
                },
                "processed_yogas": processed_yogas.yogas,  # Access the yogas list from YogasData
                "astro_aspects": {
                    "aspects": [
                        aspect.model_dump() for aspect in astro_aspects.aspects
                    ],  # Access the aspects list from PlanetaryAspectsData
                },
                "astro_exaltation": {
                    "exalted_planets": astro_exaltation.exalted_planets,  # Access from ExaltationData
                    "debilitated_planets": astro_exaltation.debilitated_planets,
                },
                "current_date": current_time,
                "timezone": "IST",  # Default to IST, could be extracted from profile
                "country": "India",  # Default, could be extracted
                "ascendant_degree": "Not specified",  # Could be extracted if available
                "datetime": datetime,  # Add datetime for date formatting in template
            }

            # Render the template
            formatted_prompt = template.render(**context)
            return formatted_prompt

        except Exception as e:
            logger.error(f"Error constructing Jinja2 prompt: {e}")
            # Fallback to simple template if Jinja2 fails
            return self._construct_simple_prompt(profile_data, current_time)

    def _construct_simple_prompt(
        self, profile_data: ProfileData, current_time: datetime
    ) -> str:
        """Construct system prompt using the original simple template for backward compatibility."""
        try:
            # Extract basic profile information
            kundli_data = profile_data.kundli_data
            basic_astro = kundli_data.get("basic_astro_details", {})

            # Create simple template with basic info
            simple_template = """You are Luna, a knowledgeable Vedic astrology assistant. You are having a conversation with a user about their astrological profile.

USER PROFILE INFORMATION:
- Name: {name}
- Birth DateTime: {birth_datetime}
- Birth Place: {birth_place}
- Sun Sign: {sun_sign}
- Moon Sign: {moon_sign}
- Gender: {gender}

Please provide helpful, accurate Vedic astrology insights based on this profile information. Be conversational, friendly, and engaging. Keep responses concise but informative (max 250 words).

Choose the most appropriate category for the user's query from: finance, health, relationships, career, education, travel, spirituality, general, or other.

IMPORTANT: Pay attention to whether the user wants to:
1. Switch to a different profile (e.g., "I want to talk about my wife", "Can we discuss my son's chart?", "Let me ask about my friend")
2. Talk about another person (e.g., "What about my mother?", "My brother's career", "My partner's health")

If the user expresses intent to switch profiles or discuss another person, set wants_to_switch_profile to true.

Remember to:
- Use the profile information provided when relevant
- Give general astrological guidance when specific data isn't available
- Be encouraging and positive in your responses
- Stay focused on Vedic astrology and spiritual growth
- Detect profile switching intent and respond appropriately"""

            # Format the template with available data
            formatted_prompt = simple_template.format(
                name=basic_astro.get("full_name", "Not provided"),
                birth_datetime=f"{basic_astro.get('day', 'N/A')}/{basic_astro.get('month', 'N/A')}/{basic_astro.get('year', 'N/A')} {basic_astro.get('hour', 'N/A')}:{basic_astro.get('minute', 'N/A')}",
                birth_place=basic_astro.get("place", "Not provided"),
                sun_sign=basic_astro.get("sunsign", "Not calculated"),
                moon_sign=basic_astro.get("moonsign", "Not calculated"),
                gender=basic_astro.get("gender", "Not provided"),
            )

            return formatted_prompt

        except Exception as e:
            logger.error(f"Error constructing simple prompt: {e}")
            return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Return a fallback prompt when profile data is not available."""
        return """You are Luna, an AI Vedic Astrology assistant. 

I'm here to help with astrological questions, but I don't have access to your specific birth chart details at the moment. 

Please provide your birth date, time, and place so I can give you personalized astrological guidance. Alternatively, you can ask general questions about Vedic astrology principles.

How can I help you today?"""
