from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

from kundli.divineapi_v2.api_response_models import (
    AscendantReportResponse,
    BasicAstroDetailsResponse,
    CompositeFriendshipResponse,
    DashaAnalysisResponse,
    GemstoneResponse,
    HoroscopeChartResponse,
    KaalSarpaDoshaResponse,
    ManglikDoshaResponse,
    PlanetAnalysisResponse,
    PlanetaryPositionsResponse,
    PlanetName,
    SadheSatiResponse,
    ShadbalaResponse,
    VimshottariDashaResponse,
    YogasResponse,
)


class EnhancedDashaAnalysis(BaseModel):
    """Enhanced dasha analysis with time and planet information"""

    analysis_type: Literal["maha", "antar"]  # Type of dasha analysis
    maha_planet: PlanetName  # The maha dasha planet
    antar_planet: Optional[PlanetName] = (
        None  # The antar dasha planet (None for maha dasha)
    )
    from_date: date  # Start date of the dasha period
    to_date: date  # End date of the dasha period
    analysis: DashaAnalysisResponse  # The actual analysis response


class RawAstroAPIData(BaseModel):
    # Basic astrological information
    basic_astro_details: BasicAstroDetailsResponse
    planetary_positions: PlanetaryPositionsResponse

    # Chart data
    horoscope_charts: Optional[Dict[str, HoroscopeChartResponse]] = (
        None  # Keyed by chart_id (D1, D9, etc.)
    )
    composite_friendship: Optional[CompositeFriendshipResponse] = None

    # Dasha and timing information
    vimshottari_dasha: Optional[VimshottariDashaResponse] = None

    # Enhanced dasha analysis with time and planet information
    dasha_analysis: Optional[List[EnhancedDashaAnalysis]] = None

    # Doshas and special conditions
    sadhe_sati: Optional[SadheSatiResponse] = None
    kaal_sarpa_dosha: Optional[KaalSarpaDoshaResponse] = None
    manglik_dosha: Optional[ManglikDoshaResponse] = None

    # Analysis and calculations
    ascendant_report: AscendantReportResponse
    yogas: Optional[YogasResponse] = None
    shadbala: Optional[ShadbalaResponse] = None
    planet_analysis: Optional[Dict[PlanetName, PlanetAnalysisResponse]] = None

    # Special features
    gemstone: Optional[GemstoneResponse] = None
