"""
Astro Utility Service for QNA Module

This service provides calculations for planetary aspects and exaltation/debilitation status
that can be used to enhance the system prompt with derived astrological information.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from kundli.divineapi_v2.api_response_models import (
    HoroscopeChartResponse,
    HouseModel,
    PlanetName,
    ZodiacSign,
)

# Define sign names mapping
SIGN_NAMES = {
    1: "Aries",
    2: "Taurus",
    3: "Gemini",
    4: "Cancer",
    5: "Leo",
    6: "Virgo",
    7: "Libra",
    8: "Scorpio",
    9: "Sagittarius",
    10: "Capricorn",
    11: "Aquarius",
    12: "Pisces",
}


class AspectType(Enum):
    """Types of planetary aspects in Vedic astrology based on house relationships."""

    SEVENTH = "7th House"  # Opposition aspect
    FOURTH = "4th House"  # Square aspect
    EIGHTH = "8th House"  # Square aspect
    THIRD = "3rd House"  # Sextile aspect
    FIFTH = "5th House"  # Trine aspect
    NINTH = "9th House"  # Trine aspect
    TENTH = "10th House"  # Square aspect


class ExaltationStatus(Enum):
    """Planetary exaltation status."""

    EXALTED = "Exalted"
    DEBILITATED = "Debilitated"
    NEUTRAL = "Neutral"


class PlanetaryAspect(BaseModel):
    """Represents an aspect between two planets."""

    planet1: str
    planet2: str
    aspect_type: AspectType
    description: str
    strength: str  # Strong, Medium, Weak


class PlanetStatus(BaseModel):
    """Represents the status of a planet including exaltation/debilitation."""

    planet: str
    sign: str
    exaltation_status: ExaltationStatus
    description: str


class HouseInfo(BaseModel):
    """Represents information about a house in a divisional chart."""

    planets: List[str]
    sign_name: str


class DivisionalChartData(BaseModel):
    """Represents processed data from a divisional chart."""

    houses: Dict[int, HouseInfo]


class VimshottariDashaData(BaseModel):
    """Represents processed vimshottari dasha data."""

    current_maha_dasha: Optional["MahaDashaInfo"] = None
    current_antar_dasha: Optional["AntarDashaInfo"] = None
    future_antar_dashas: List["AntarDashaInfo"] = []


class MahaDashaInfo(BaseModel):
    """Represents information about a maha dasha period."""

    planet: str
    start_date: date
    end_date: date


class AntarDashaInfo(BaseModel):
    """Represents information about an antar dasha period."""

    maha_planet: str
    antar_planet: str
    start_date: date
    end_date: date


class YogasData(BaseModel):
    """Represents processed yogas data."""

    yogas: List[str]


class PlanetaryAspectsData(BaseModel):
    """Represents processed planetary aspects data."""

    aspects: List[PlanetaryAspect]


class ExaltationData(BaseModel):
    """Represents processed exaltation data."""

    exalted_planets: List[str]
    debilitated_planets: List[str]


class AstroUtilsService:
    """Service for calculating planetary aspects and exaltation/debilitation."""

    # Exaltation and debilitation signs for planets (traditional Vedic astrology)
    EXALTATION_SIGNS = {
        PlanetName.Sun: ZodiacSign.ARIES,
        PlanetName.Moon: ZodiacSign.TAURUS,
        PlanetName.Mars: ZodiacSign.CAPRICORN,
        PlanetName.Mercury: ZodiacSign.VIRGO,
        PlanetName.Jupiter: ZodiacSign.CANCER,
        PlanetName.Venus: ZodiacSign.PISCES,
        PlanetName.Saturn: ZodiacSign.LIBRA,
        PlanetName.Rahu: ZodiacSign.TAURUS,  # Rahu is exalted in Taurus
        PlanetName.Ketu: ZodiacSign.SCORPIO,  # Ketu is exalted in Scorpio
    }

    DEBILITATION_SIGNS = {
        PlanetName.Sun: ZodiacSign.LIBRA,
        PlanetName.Moon: ZodiacSign.SCORPIO,
        PlanetName.Mars: ZodiacSign.CANCER,
        PlanetName.Mercury: ZodiacSign.PISCES,
        PlanetName.Jupiter: ZodiacSign.CAPRICORN,
        PlanetName.Venus: ZodiacSign.VIRGO,
        PlanetName.Saturn: ZodiacSign.ARIES,
        PlanetName.Rahu: ZodiacSign.SCORPIO,  # Rahu is debilitated in Scorpio
        PlanetName.Ketu: ZodiacSign.TAURUS,  # Ketu is debilitated in Taurus
    }

    # House aspects for planets (traditional Vedic astrology)
    PLANETARY_ASPECTS = {
        PlanetName.Sun: [7],  # Sun aspects 7th house
        PlanetName.Moon: [7],  # Moon aspects 7th house
        PlanetName.Mars: [4, 7, 8],  # Mars aspects 4th, 7th, and 8th houses
        PlanetName.Mercury: [7],  # Mercury aspects 7th house
        PlanetName.Jupiter: [5, 7, 9],  # Jupiter aspects 5th, 7th, and 9th houses
        PlanetName.Venus: [7],  # Venus aspects 7th house
        PlanetName.Saturn: [3, 7, 10],  # Saturn aspects 3rd, 7th, and 10th houses
        PlanetName.Rahu: [5, 7, 9],  # Rahu aspects 5th, 7th, and 9th houses
        PlanetName.Ketu: [5, 7, 9],  # Ketu aspects 5th, 7th, and 9th houses
    }

    def __init__(self):
        pass

    def preprocess_divisional_chart_data(
        self,
        horoscope_charts: Optional[Dict[str, HoroscopeChartResponse]],
        chart_type: str,
    ) -> DivisionalChartData:
        """Preprocess divisional chart data to extract house-wise planet information.

        Args:
            horoscope_charts: Dictionary containing various divisional charts
            chart_type: Type of divisional chart (e.g., "D9" for navamsa, "D10" for dashamsa)

        Returns:
            DivisionalChartData with processed house information
        """
        if not horoscope_charts or chart_type not in horoscope_charts:
            return DivisionalChartData(houses={})

        chart_data = horoscope_charts[chart_type]
        if not chart_data or chart_data.data is None:
            return DivisionalChartData(houses={})

        house_data: Dict[str, HouseModel] = chart_data.data
        processed_houses = {}

        for house_num in range(1, 13):
            house_key = str(house_num)
            if house_key in house_data:
                house_info = house_data[house_key]
                planets_in_house = []

                if house_info.planet:
                    for planet_info in house_info.planet:
                        if planet_info.name:
                            # Extract the planet name value from the PlanetName enum
                            planet_name = (
                                planet_info.name.value
                                if hasattr(planet_info.name, "value")
                                else str(planet_info.name)
                            )
                            # Skip outer planets (Uranus, Neptune, Pluto)
                            if planet_name not in [
                                "Uranus",
                                "Neptune",
                                "Pluto",
                                "Unknown",
                            ]:
                                planets_in_house.append(planet_name)

                # Convert sign number to sign name
                sign_name = SIGN_NAMES.get(
                    house_info.sign_no, f"Sign {house_info.sign_no}"
                )

                processed_houses[house_num] = HouseInfo(
                    planets=planets_in_house,
                    sign_name=sign_name,
                )
            else:
                processed_houses[house_num] = HouseInfo(
                    planets=[], sign_name="Not specified"
                )

        return DivisionalChartData(houses=processed_houses)

    def preprocess_navamsa_data(
        self, horoscope_charts: Optional[Dict[str, HoroscopeChartResponse]]
    ) -> DivisionalChartData:
        """Preprocess navamsa (D9) data to extract house-wise planet information.

        This is a convenience method that calls preprocess_divisional_chart_data with "D9".
        """
        return self.preprocess_divisional_chart_data(horoscope_charts, "D9")

    def preprocess_vimshottari_dasha(
        self, vimshottari_data: Any
    ) -> VimshottariDashaData:
        """Preprocess vimshottari dasha data to identify current and future periods."""
        if not vimshottari_data or not vimshottari_data.maha_dasha:
            return VimshottariDashaData()

        current_date = datetime.now().date()
        future_antar_dashas = []
        current_maha_dasha = None
        current_antar_dasha = None

        # Parse through all maha dashas to find current and future periods
        for maha_dasha_planet, maha_dasha_data in vimshottari_data.maha_dasha.items():
            if (
                not maha_dasha_data
                or not maha_dasha_data.start_date
                or not maha_dasha_data.end_date
            ):
                continue

            maha_dasha_start = maha_dasha_data.start_date
            maha_dasha_end = maha_dasha_data.end_date

            # Check if current date falls within this maha dasha
            if maha_dasha_start <= current_date <= maha_dasha_end:
                current_maha_dasha = MahaDashaInfo(
                    planet=(
                        maha_dasha_planet.value
                        if hasattr(maha_dasha_planet, "value")
                        else str(maha_dasha_planet)
                    ),
                    start_date=maha_dasha_start,
                    end_date=maha_dasha_end,
                )

                # Find current antar dasha within this maha dasha
                if maha_dasha_data.antar_dasha:
                    for antar_planet, antar_data in maha_dasha_data.antar_dasha.items():
                        if (
                            not antar_data
                            or not antar_data.start_time
                            or not antar_data.end_time
                        ):
                            continue

                        antar_start = antar_data.start_time
                        antar_end = antar_data.end_time

                        # Check if current date falls within this antar dasha
                        if antar_start <= current_date <= antar_end:
                            current_antar_dasha = AntarDashaInfo(
                                maha_planet=(
                                    maha_dasha_planet.value
                                    if hasattr(maha_dasha_planet, "value")
                                    else str(maha_dasha_planet)
                                ),
                                antar_planet=(
                                    antar_planet.value
                                    if hasattr(antar_planet, "value")
                                    else str(antar_planet)
                                ),
                                start_date=antar_start,
                                end_date=antar_end,
                            )

                            # Add future antar dashas from this maha dasha (next 5 years)
                            future_limit = datetime(
                                current_date.year + 5,
                                current_date.month,
                                current_date.day,
                            ).date()

                            for (
                                future_antar_planet,
                                future_antar_data,
                            ) in maha_dasha_data.antar_dasha.items():
                                if (
                                    not future_antar_data
                                    or not future_antar_data.start_time
                                    or not future_antar_data.end_time
                                ):
                                    continue

                                # Only include future antar dashas within 5 years
                                if (
                                    future_antar_data.start_time > current_date
                                    and future_antar_data.start_time <= future_limit
                                ):
                                    future_antar_dashas.append(
                                        AntarDashaInfo(
                                            maha_planet=(
                                                maha_dasha_planet.value
                                                if hasattr(maha_dasha_planet, "value")
                                                else str(maha_dasha_planet)
                                            ),
                                            antar_planet=(
                                                future_antar_planet.value
                                                if hasattr(future_antar_planet, "value")
                                                else str(future_antar_planet)
                                            ),
                                            start_date=future_antar_data.start_time,
                                            end_date=future_antar_data.end_time,
                                        )
                                    )
                            break

                # If no current antar dasha found, look for future ones
                if not current_antar_dasha:
                    future_limit = datetime(
                        current_date.year + 5, current_date.month, current_date.day
                    ).date()

                    for antar_planet, antar_data in maha_dasha_data.antar_dasha.items():
                        if (
                            not antar_data
                            or not antar_data.start_time
                            or not antar_data.end_time
                        ):
                            continue

                        # Include future antar dashas within 5 years
                        if (
                            antar_data.start_time > current_date
                            and antar_data.start_time <= future_limit
                        ):
                            future_antar_dashas.append(
                                AntarDashaInfo(
                                    maha_planet=(
                                        maha_dasha_planet.value
                                        if hasattr(maha_dasha_planet, "value")
                                        else str(maha_dasha_planet)
                                    ),
                                    antar_planet=(
                                        antar_planet.value
                                        if hasattr(antar_planet, "value")
                                        else str(antar_planet)
                                    ),
                                    start_date=antar_data.start_time,
                                    end_date=antar_data.end_time,
                                )
                            )
                break

            # If this maha dasha is in the future, check for future antar dashas
            elif maha_dasha_start > current_date:
                future_limit = datetime(
                    current_date.year + 5, current_date.month, current_date.day
                ).date()

                if maha_dasha_start <= future_limit and maha_dasha_data.antar_dasha:
                    for antar_planet, antar_data in maha_dasha_data.antar_dasha.items():
                        if (
                            not antar_data
                            or not antar_data.start_time
                            or not antar_data.end_time
                        ):
                            continue

                        # Include future antar dashas within 5 years
                        if (
                            antar_data.start_time > current_date
                            and antar_data.start_time <= future_limit
                        ):
                            future_antar_dashas.append(
                                AntarDashaInfo(
                                    maha_planet=(
                                        maha_dasha_planet.value
                                        if hasattr(maha_dasha_planet, "value")
                                        else str(maha_dasha_planet)
                                    ),
                                    antar_planet=(
                                        antar_planet.value
                                        if hasattr(antar_planet, "value")
                                        else str(antar_planet)
                                    ),
                                    start_date=antar_data.start_time,
                                    end_date=antar_data.end_time,
                                )
                            )

        # Sort future antar dashas by start date
        future_antar_dashas.sort(key=lambda x: x.start_date)

        return VimshottariDashaData(
            current_maha_dasha=current_maha_dasha,
            current_antar_dasha=current_antar_dasha,
            future_antar_dashas=future_antar_dashas,
        )

    def preprocess_yogas(self, yogas_data: Any) -> YogasData:
        """Preprocess yogas data to extract only the names of valid yogas."""
        if not yogas_data:
            return YogasData(yogas=[])

        yogas = []

        # Helper function to check if a yoga is valid
        def is_yoga_valid(yoga_data):
            if not yoga_data:
                return False
            if hasattr(yoga_data, "is_valid"):
                return yoga_data.is_valid
            return True  # Assume valid if no is_valid field

        # Check all individual yogas
        yoga_fields = [
            "raj_yoga",
            "vipreet_raj_yoga",
            "dhan_yoga",
            "buddha_aditya_yoga",
            "gaja_kesari_yoga",
            "amala_yoga",
            "parvata_yoga",
            "kahala_yoga",
            "chamara_yoga",
            "sankha_yoga",
            "lagnadhi_yoga",
            "chandradhi_yoga",
            "shubh_kartari_yoga",
            "paap_kartari_yoga",
            "saraswati_yoga",
            "lakshmi_yoga",
            "kusuma_yoga",
            "kalindi_yoga",
            "kalpadruma_yoga",
            "khadga_yoga",
            "koorma_yoga",
            "matsya_yoga",
            "sarada_yoga",
            "srinatha_yoga",
            "mridanga_yoga",
            "bheri_yoga",
        ]

        for yoga_field in yoga_fields:
            yoga_data = getattr(yogas_data, yoga_field, None)
            if is_yoga_valid(yoga_data) and yoga_data is not None:
                yoga_name = (
                    yoga_data.name
                    if hasattr(yoga_data, "name") and yoga_data.name
                    else yoga_field.replace("_", " ").title()
                )
                yogas.append(yoga_name)

        # Check pancha mahapurusha yogas
        if yogas_data.pancha_mahapurusha_yoga:
            pancha_fields = [
                "bhadra_pancha_mahapurusha_yoga",
                "malavya_pancha_mahapurusha_yoga",
                "ruchaka_pancha_mahapurusha_yoga",
                "hamsa_pancha_mahapurusha_yoga",
                "sasha_pancha_mahapurusha_yoga",
            ]
            for pancha_field in pancha_fields:
                pancha_data = getattr(
                    yogas_data.pancha_mahapurusha_yoga, pancha_field, None
                )
                if is_yoga_valid(pancha_data) and pancha_data is not None:
                    yoga_name = (
                        pancha_data.name
                        if hasattr(pancha_data, "name") and pancha_data.name
                        else pancha_field.replace("_", " ").title()
                    )
                    yogas.append(yoga_name)

        # Check lunar yogas
        if yogas_data.lunar_yoga:
            lunar_fields = ["sunapha_yoga", "anapha_yoga", "duradhara_yoga"]
            for lunar_field in lunar_fields:
                lunar_data = getattr(yogas_data.lunar_yoga, lunar_field, None)
                if is_yoga_valid(lunar_data) and lunar_data is not None:
                    yoga_name = (
                        lunar_data.name
                        if hasattr(lunar_data, "name") and lunar_data.name
                        else lunar_field.replace("_", " ").title()
                    )
                    yogas.append(yoga_name)

        # Check solar yogas
        if yogas_data.solar_yoga:
            solar_fields = ["vesi_yoga", "vasi_yoga", "ubhayachari_yoga"]
            for solar_field in solar_fields:
                solar_data = getattr(yogas_data.solar_yoga, solar_field, None)
                if is_yoga_valid(solar_data) and solar_data is not None:
                    yoga_name = (
                        solar_data.name
                        if hasattr(solar_data, "name") and solar_data.name
                        else solar_field.replace("_", " ").title()
                    )
                    yogas.append(yoga_name)

        # Check trimurti yogas
        if yogas_data.trimurti_yogas:
            trimurti_fields = ["hari_yoga", "hara_yoga", "brahma_yoga"]
            for trimurti_field in trimurti_fields:
                trimurti_data = getattr(yogas_data.trimurti_yogas, trimurti_field, None)
                if is_yoga_valid(trimurti_data) and trimurti_data is not None:
                    yoga_name = (
                        trimurti_data.name
                        if hasattr(trimurti_data, "name") and trimurti_data.name
                        else trimurti_field.replace("_", " ").title()
                    )
                    yogas.append(yoga_name)

        return YogasData(yogas=yogas)

    def calculate_planetary_aspects(self, planets: List[Any]) -> List[PlanetaryAspect]:
        """
        Calculate aspects between planets based on their house positions and traditional Vedic rules.

        Args:
            planets: List of planets with their positions

        Returns:
            List of planetary aspects
        """
        aspects = []

        if not planets:
            return aspects

        # Create a mapping of planet names to house numbers
        planet_houses = {}
        for planet in planets:
            if planet.name and planet.house:
                planet_name = (
                    planet.name.value
                    if hasattr(planet.name, "value")
                    else str(planet.name)
                )
                planet_houses[planet_name] = planet.house

        # Calculate aspects based on PLANETARY_ASPECTS rules
        for planet1_name, planet1_house in planet_houses.items():
            # Get the aspecting houses for this planet
            planet1_enum = self._get_planet_enum(planet1_name)
            if planet1_enum and planet1_enum in self.PLANETARY_ASPECTS:
                aspecting_houses = self.PLANETARY_ASPECTS[planet1_enum]

                # Calculate which houses this planet aspects relative to its position
                for aspect_offset in aspecting_houses:
                    # Calculate the actual house number that is being aspected
                    # aspect_offset is the relative house number from the planet's position
                    # For example: planet in house 6 aspects 7th house = house 12
                    aspecting_house = (planet1_house + aspect_offset - 1) % 12
                    if aspecting_house == 0:
                        aspecting_house = 12

                    # Find planets in the aspected house
                    for planet2_name, planet2_house in planet_houses.items():
                        if (
                            planet1_name != planet2_name
                            and planet2_house == aspecting_house
                        ):
                            # Create aspect based on house relationship
                            aspect_type = self._get_aspect_type_for_house(aspect_offset)
                            strength = self._get_aspect_strength(aspect_offset)

                            aspect = PlanetaryAspect(
                                planet1=planet1_name,
                                planet2=planet2_name,
                                aspect_type=aspect_type,
                                description=f"{planet1_name} in house {planet1_house} aspects {planet2_name} in house {planet2_house}",
                                strength=strength,
                            )
                            aspects.append(aspect)

        return aspects

    def _get_planet_enum(self, planet_name: str) -> Optional[PlanetName]:
        """Convert planet name string to PlanetName enum."""
        try:
            return PlanetName(planet_name)
        except ValueError:
            return None

    def _get_aspect_type_for_house(self, house: int) -> AspectType:
        """Get the aspect type for a given house number."""
        if house == 7:
            return AspectType.SEVENTH
        elif house == 4:
            return AspectType.FOURTH
        elif house == 8:
            return AspectType.EIGHTH
        elif house == 3:
            return AspectType.THIRD
        elif house == 5:
            return AspectType.FIFTH
        elif house == 9:
            return AspectType.NINTH
        elif house == 10:
            return AspectType.TENTH
        else:
            return AspectType.SEVENTH  # Default fallback

    def _get_aspect_strength(self, house: int) -> str:
        """Get the strength of an aspect based on house number."""
        if house in [7, 4, 8, 5, 9, 10]:
            return "Strong"
        elif house in [3, 11]:
            return "Medium"
        else:
            return "Weak"

    def calculate_exaltation_status(self, planets: List[Any]) -> List[PlanetStatus]:
        """
        Calculate exaltation/debilitation status for planets.

        Args:
            planets: List of planets with their positions

        Returns:
            List of planet statuses
        """
        planet_statuses = []

        for planet in planets:
            if not planet.name or not planet.sign:
                continue

            planet_name = (
                planet.name.value if hasattr(planet.name, "value") else str(planet.name)
            )
            planet_sign = (
                planet.sign.value if hasattr(planet.sign, "value") else str(planet.sign)
            )

            # Skip outer planets that don't have traditional exaltation/debilitation
            if planet_name in ["Uranus", "Neptune", "Pluto"]:
                continue

            # Check if planet is exalted or debilitated
            exaltation_status = ExaltationStatus.NEUTRAL
            description = f"{planet_name} is in {planet_sign} (neutral position)"

            # Convert string planet name back to PlanetName enum for lookup
            try:
                planet_enum = PlanetName(planet_name)
                if planet_enum in self.EXALTATION_SIGNS:
                    if planet_sign == self.EXALTATION_SIGNS[planet_enum].value:
                        exaltation_status = ExaltationStatus.EXALTED
                        description = f"{planet_name} is exalted in {planet_sign} (very strong position)"
                    elif (
                        planet_enum in self.DEBILITATION_SIGNS
                        and planet_sign == self.DEBILITATION_SIGNS[planet_enum].value
                    ):
                        exaltation_status = ExaltationStatus.DEBILITATED
                        description = f"{planet_name} is debilitated in {planet_sign} (weak position)"
            except ValueError:
                # Planet name not in enum, keep as neutral
                pass

            planet_status = PlanetStatus(
                planet=planet_name,
                sign=planet_sign,
                exaltation_status=exaltation_status,
                description=description,
            )
            planet_statuses.append(planet_status)

        return planet_statuses

    def get_exaltation_summary(self, planet_statuses: List[PlanetStatus]) -> str:
        """
        Generate a summary of planetary exaltation statuses.

        Args:
            planet_statuses: List of planet statuses

        Returns:
            Formatted summary string
        """
        if not planet_statuses:
            return "Planetary status information not available."

        # Group by status
        exalted = [
            ps.planet
            for ps in planet_statuses
            if ps.exaltation_status == ExaltationStatus.EXALTED
        ]
        debilitated = [
            ps.planet
            for ps in planet_statuses
            if ps.exaltation_status == ExaltationStatus.DEBILITATED
        ]

        summary_parts = []
        if exalted:
            summary_parts.append(f"Exalted: {', '.join(exalted)}")
        if debilitated:
            summary_parts.append(f"Debilitated: {', '.join(debilitated)}")

        if not summary_parts:
            return "All planets are in neutral positions."

        return "; ".join(summary_parts)

    def get_detailed_aspects_for_template(
        self, planets: List[Any]
    ) -> PlanetaryAspectsData:
        """
        Get detailed aspect information formatted for the Jinja2 template.

        Args:
            planets: List of planets with their positions

        Returns:
            PlanetaryAspectsData with aspects and summary for template use
        """
        aspects = self.calculate_planetary_aspects(planets)

        return PlanetaryAspectsData(
            aspects=aspects,
        )

    def get_detailed_exaltation_for_template(
        self, planets: List[Any]
    ) -> ExaltationData:
        """
        Get simplified exaltation information formatted for the Jinja2 template.

        Args:
            planets: List of planets with their positions

        Returns:
            ExaltationData with exaltation summary and counts for template use
        """
        planet_statuses = self.calculate_exaltation_status(planets)

        # Get lists of exalted and debilitated planets
        exalted_planets = [
            ps.planet
            for ps in planet_statuses
            if ps.exaltation_status == ExaltationStatus.EXALTED
        ]
        debilitated_planets = [
            ps.planet
            for ps in planet_statuses
            if ps.exaltation_status == ExaltationStatus.DEBILITATED
        ]

        return ExaltationData(
            exalted_planets=exalted_planets,
            debilitated_planets=debilitated_planets,
        )
