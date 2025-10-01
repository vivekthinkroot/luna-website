from datetime import date, datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dao.geolocation import GeolocationDAO
from dao.profiles import ProfileDAO
from kundli.divineapi_v2.api_response_models import Gender
from kundli.divineapi_v2.client_v2 import APIConfig, DivineAPIClientV2, UserProfile
from kundli.divineapi_v2.output_model import RawAstroAPIData
from utils.logger import get_logger

logger = get_logger()


class ChartStyle(str, Enum):
    """Chart style for kundli generation."""

    AUTO = "auto"
    SOUTH = "south"
    NORTH = "north"


class BasicKundliInfo(BaseModel):
    """Simplified kundli information containing essential astrological details."""
    
    person_name: str
    date_of_birth: str  # Format: "DD-MMM-YYYY"
    birth_star: str  # Nakshatra name
    birth_star_pada: Optional[str] = None  # Pada (1st, 2nd, 3rd, or 4th)
    moon_sign: str  # Rashi
    paksha: str  # Shukla/Krishna paksha
    lagna: str  # Ascendant's sign
    current_maha_dasha_planet: Optional[str] = None  # Current maha dasha planet name
    current_maha_dasha_start_date: Optional[str] = None  # Current maha dasha start date (Format: "DD-MMM-YYYY")
    current_maha_dasha_end_date: Optional[str] = None  # Current maha dasha end date (Format: "DD-MMM-YYYY")


async def build_and_store_astro_profile_data(
    profile_id: str,
    chart_style: Optional[ChartStyle] = ChartStyle.AUTO,
) -> BasicKundliInfo:
    """
    Generate astrological data for a profile and store it in the database.

    This function checks if profile data already exists and only makes external API calls
    when the profile has been modified after the profile data was last updated.

    Args:
        profile_id: ID of the profile to generate astro data for
        chart_style: Chart style preference (auto/south/north)

    Returns:
        BasicKundliInfo: Simplified kundli information containing essential astrological details

    Raises:
        ValueError: If profile or location data is missing
    """
    # 1. fetch profile and location details
    profiles_dao = ProfileDAO()
    geolocation_dao = GeolocationDAO()

    profile = profiles_dao.get_profile_by_id(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    if not profile.birth_datetime or not profile.birth_place or not profile.gender:
        raise ValueError(
            "Profile is missing required birth details (datetime/place/gender)"
        )
    if not profile.birth_location_id:
        raise ValueError(
            "Profile is missing birth location reference (birth_location_id)"
        )

    # 2. Check if profile data already exists and if it's up-to-date
    existing_profile_data = profiles_dao.get_profile_data(profile_id)

    if existing_profile_data:
        # Ensure both datetimes are timezone-aware
        def ensure_aware(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                try:
                    dt_obj = datetime.fromisoformat(dt)
                except Exception:
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                        try:
                            dt_obj = datetime.strptime(dt, fmt)
                            break
                        except Exception:
                            continue
                    else:
                        raise ValueError(f"Could not parse datetime string: {dt}")
                dt = dt_obj
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                return dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        updated_at_1 = ensure_aware(profile.updated_at)
        updated_at_2 = ensure_aware(existing_profile_data.updated_at)
        # Check if profile was modified after the profile data was updated
        if updated_at_1 <= updated_at_2:
            logger.info(
                f"Profile data for {profile_id} is up-to-date. Using stored data."
            )
            # Convert the stored JSON data back to RawAstroAPIData
            try:
                raw_data = RawAstroAPIData.model_validate(existing_profile_data.kundli_data)
                return _extract_basic_kundli_info(raw_data)
            except Exception as e:
                logger.warning(
                    f"Failed to parse cached profile data for {profile_id}, regenerating: {e}"
                )
                # If parsing fails, continue to regenerate the data
        else:
            logger.info(
                f"Profile {profile_id} was modified after profile data was updated. Rebuilding data."
            )

    # 3. Profile data doesn't exist or is outdated, so generate new data
    location = geolocation_dao.get_location_by_id(profile.birth_location_id)
    if not location:
        raise ValueError("Birth location not found for provided birth_location_id")

    # Determine the actual chart style based on location if AUTO is selected
    if chart_style == ChartStyle.AUTO:
        chart_style = _determine_chart_style_from_location(location)

    full_name = profile.name or "User"
    birth_datetime = profile.birth_datetime
    gender = (
        profile.gender.value
        if hasattr(profile.gender, "value")
        else str(profile.gender)
    )
    birth_place = profile.birth_place
    latitude = str(location.latitude)
    longitude = str(location.longitude)
    timezone_iana = location.timezone

    # 4. generate the astro payload
    astro_payload = await _build_kundli_data_from_divineapi(
        full_name,
        birth_datetime,
        gender,
        birth_place,
        latitude,
        longitude,
        timezone_iana,
        chart_style.value if chart_style else "south",
    )
    logger.info(
        f"Astrology data generated successfully for profile {profile_id} ({full_name})!"
    )

    # 5. Store astro data in database
    try:
        # Convert RawAstroAPIData to dict for storage with JSON-compatible serialization
        # This ensures datetime objects are converted to ISO format strings
        kundli_data = astro_payload.model_dump(mode="json")

        profiles_dao.store_kundli_data(
            profile_id=profile_id, kundli_data=kundli_data
        )
        logger.info(
            f"Astrology data stored successfully for profile {profile_id} in profile_data table"
        )
    except Exception as e:
        logger.error(f"Failed to store astrology data for profile {profile_id}: {e}")
        # Continue execution even if storage fails - we still return the generated data

    # 6. Extract and return simplified kundli info
    return _extract_basic_kundli_info(astro_payload)


def _determine_chart_style_from_location(location) -> ChartStyle:
    """
    Determine chart style based on location.

    Args:
        location: LocationCandidate object with location details

    Returns:
        ChartStyle: SOUTH if location is in South India, NORTH otherwise
    """
    # South Indian states and union territories
    south_india_states = {
        "Andhra Pradesh",
        "Telangana",
        "Karnātaka",
        "Kerala",
        "Tamil Nādu",
        "Puducherry",
        "Lakshadweep",
        "Andaman and Nicobar Islands",
    }

    # Check if the location is in South India
    if location.province and location.province in south_india_states:
        return ChartStyle.SOUTH

    # If province is not available, use latitude as a fallback
    # South India is roughly below 20°N latitude
    if location.latitude < 20.0:
        return ChartStyle.SOUTH

    return ChartStyle.NORTH


async def _build_kundli_data_from_divineapi(
    full_name: str,
    birth_datetime: datetime,
    gender: str,
    birth_place: str,
    latitude: str,
    longitude: str,
    timezone_iana: Optional[str] = None,
    chart_style: Optional[str] = "south",
) -> RawAstroAPIData:
    """Generate kundli using a datetime object for birth details.
    Args:
        full_name (str): Full name of the person.
        birth_datetime (datetime): Datetime object representing date and time of birth (typically UTC from PostgreSQL timestampz).
        gender (str): Gender of the person.
        birth_place (str): Place of birth.
        lat (str): Latitude of the place.
        lon (str): Longitude of the place.
        timezone_iana (Optional[str]): IANA timezone identifier (e.g., "Asia/Kolkata", "America/New_York"). The birth_datetime will be converted to this timezone for date/time component extraction.
        chart_style (Optional[str]): Style of chart to generate (south/north).
    Returns:
        RawAstroAPIData: The raw astrological data from the Divine API client.
    """

    # Convert birth_datetime (assumed UTC from PostgreSQL) to the specified timezone and extract components
    if timezone_iana is not None:
        try:
            tz = ZoneInfo(timezone_iana)
            # Convert UTC datetime to the specified timezone
            localized_datetime = birth_datetime.astimezone(tz)
            # Get timezone offset in decimal hours
            offset = tz.utcoffset(localized_datetime)
            tzone_value = offset.total_seconds() / 3600 if offset else 5.5
        except (ValueError, AttributeError):
            # Fallback: try to parse as numeric string, otherwise use default
            try:
                tzone_value = float(timezone_iana)
            except (ValueError, TypeError):
                tzone_value = 5.5
            localized_datetime = birth_datetime
    else:
        # No timezone specified, use birth_datetime as-is and default timezone
        localized_datetime = birth_datetime
        tzone_value = 5.5

    # Convert gender string to Gender enum
    gender_enum = Gender.MALE if gender.lower() in ["male", "m", "1"] else Gender.FEMALE

    # Create UserProfile object for the v2 client
    user_profile = UserProfile(
        full_name=full_name,
        day=localized_datetime.day,
        month=localized_datetime.month,
        year=localized_datetime.year,
        hour=localized_datetime.hour,
        min=localized_datetime.minute,
        sec=localized_datetime.second,
        gender=gender_enum,
        place=birth_place,
        lat=float(latitude),
        lon=float(longitude),
        tzone=tzone_value,
    )

    # Create API configuration with proper chart style validation
    chart_style_valid = "north" if chart_style == "north" else "south"
    api_config = APIConfig(
        charts=["D1", "D9"],
        chart_style=chart_style_valid,
        dasha_analysis_years=5,
    )

    client = DivineAPIClientV2()
    raw_astro_data = await client.fetch_all_astro_data(user_profile, api_config)

    return raw_astro_data


def _extract_basic_kundli_info(raw_data: RawAstroAPIData) -> BasicKundliInfo:
    """
    Extract simplified kundli information from raw astrological data.
    
    Args:
        raw_data: RawAstroAPIData containing all astrological information
        
    Returns:
        BasicKundliInfo: Simplified kundli information
    """
    basic_details = raw_data.basic_astro_details
    planetary_positions = raw_data.planetary_positions
    
    # Format date of birth as dd-mmm-yyyy
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if basic_details.month is not None:
        dob = f"{basic_details.day:02d}-{month_names[basic_details.month - 1]}-{basic_details.year}"
    else:
        dob = "Unknown"
    
    # Extract birth star and pada from Moon's planetary position
    birth_star = basic_details.nakshatra or "Unknown"
    birth_star_pada = None
    
    # Find Moon in planetary positions to get nakshatra pada
    for planet in planetary_positions.planets:
        if planet.name and planet.name.value == "Moon":
            if planet.nakshatra_pada:
                birth_star_pada = str(planet.nakshatra_pada)
            break
    
    # Extract moon sign (rashi)
    moon_sign = basic_details.moonsign.value if basic_details.moonsign else "Unknown"
    
    # Extract paksha
    paksha = basic_details.paksha or "Unknown"
    
    # Extract lagna from Ascendant's planetary position
    lagna = "Unknown"
    for planet in planetary_positions.planets:
        if planet.name and planet.name.value == "Ascendant":
            if planet.sign:
                lagna = planet.sign.value
            break
    
    # Extract current maha dasha information from vimshottari dasha
    current_maha_dasha_planet = None
    current_maha_dasha_start_date = None
    current_maha_dasha_end_date = None

    if raw_data.vimshottari_dasha and raw_data.vimshottari_dasha.maha_dasha:
        # Use today's actual date for dasha calculation
        current_date = date.today()
        
        # Find which maha dasha period contains the current date
        for planet_name, maha_dasha_data in raw_data.vimshottari_dasha.maha_dasha.items():
            if (maha_dasha_data.start_date and maha_dasha_data.end_date and
                maha_dasha_data.start_date <= current_date <= maha_dasha_data.end_date):
                current_maha_dasha_planet = planet_name.value if hasattr(planet_name, 'value') else str(planet_name)
                
                # Format maha dasha dates in dd-mmm-yyyy format for consistency
                if maha_dasha_data.start_date:
                    start_month = month_names[maha_dasha_data.start_date.month - 1]
                    current_maha_dasha_start_date = f"{maha_dasha_data.start_date.day:02d}-{start_month}-{maha_dasha_data.start_date.year}"
                
                if maha_dasha_data.end_date:
                    end_month = month_names[maha_dasha_data.end_date.month - 1]
                    current_maha_dasha_end_date = f"{maha_dasha_data.end_date.day:02d}-{end_month}-{maha_dasha_data.end_date.year}"
                break

    return BasicKundliInfo(
        person_name=basic_details.full_name or "Unknown",
        date_of_birth=dob,
        birth_star=birth_star,
        birth_star_pada=birth_star_pada,
        moon_sign=moon_sign,
        paksha=paksha,
        lagna=lagna,
        current_maha_dasha_planet=current_maha_dasha_planet,
        current_maha_dasha_start_date=current_maha_dasha_start_date,
        current_maha_dasha_end_date=current_maha_dasha_end_date
    )
