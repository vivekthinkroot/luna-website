import asyncio
from datetime import date
from typing import Any, Dict, List, Literal, Optional

import httpx
from pydantic import BaseModel, Field, field_validator

from config.settings import get_settings
from kundli.divineapi_v2.api_response_models import (
    AscendantReportResponse,
    BasicAstroDetailsResponse,
    CompositeFriendshipResponse,
    DashaAnalysisResponse,
    GemstoneResponse,
    Gender,
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
from kundli.divineapi_v2.output_model import EnhancedDashaAnalysis, RawAstroAPIData


class APIConfig(BaseModel):
    """Configuration flags for which APIs to invoke"""

    # Core data
    basic_details: bool = Field(default=True, description="Enable basic astro details")
    planetary_positions: bool = Field(
        default=True, description="Enable planetary positions"
    )
    ascendant_report: bool = Field(default=True, description="Enable ascendant report")

    # Charts - single config for all chart types
    charts: List[str] = Field(
        default=["D1", "D9"], description="List of chart types to generate"
    )
    chart_style: Literal["south", "north"] = Field(
        default="south", description="Chart style preference"
    )

    # Dasha systems
    vimshottari_dasha: bool = Field(
        default=True, description="Enable vimshottari dasha"
    )

    # Dasha analysis
    dasha_analysis: bool = Field(default=True, description="Enable dasha analysis")
    dasha_analysis_years: int = Field(
        default=5, description="Number of years to look ahead for future antar dashas"
    )

    # Doshas and special conditions
    sadhe_sati: bool = Field(default=True, description="Enable sadhe sati analysis")
    kaal_sarpa_dosha: bool = Field(
        default=True, description="Enable kaal sarpa dosha analysis"
    )
    manglik_dosha: bool = Field(
        default=True, description="Enable manglik dosha analysis"
    )

    # Analysis and calculations
    yogas: bool = Field(default=True, description="Enable yogas analysis")
    shadbala: bool = Field(default=True, description="Enable shadbala analysis")
    planet_analysis: bool = Field(default=True, description="Enable planet analysis")

    # Special features
    gemstone: bool = Field(default=True, description="Enable gemstone suggestions")
    composite_friendship: bool = Field(
        default=True, description="Enable composite friendship analysis"
    )

    @field_validator("charts", mode="after")
    @classmethod
    def set_default_charts(cls, v):
        """Set default values for charts if None or empty"""
        if v is None or len(v) == 0:
            return ["D1", "D9"]
        return v

    @field_validator("chart_style", mode="after")
    @classmethod
    def validate_chart_style(cls, v):
        """Validate chart style and set default if invalid"""
        if v not in ["south", "north"]:
            return "south"  # Use south as default if invalid
        return v

    model_config = {
        "extra": "forbid"
    }  # This ensures error if unknown attributes are passed


class UserProfile(BaseModel):
    """User profile data for astrological calculations

    Example usage:
        from kundli.divineapi_v2.client_v2 import UserProfile
        from kundli.divineapi_v2.api_response_models import Gender

        profile = UserProfile(
            full_name="John Doe",
            day=15,
            month=6,
            year=1990,
            hour=14,
            min=30,
            sec=0,
            gender=Gender.MALE,
            place="New Delhi, India",
            lat=28.6139,
            lon=77.2090,
            tzone=5.5
        )

        # Use with client
        client = DivineAPIClientV2()
        result = await client.fetch_all_astro_data(profile)
    """

    full_name: str = Field(..., description="Full name of the person")
    day: int = Field(..., ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(..., ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(..., ge=1900, le=2100, description="Year of birth")
    hour: int = Field(..., ge=0, le=23, description="Hour of birth (0-23)")
    min: int = Field(..., ge=0, le=59, description="Minute of birth (0-59)")
    sec: int = Field(..., ge=0, le=59, description="Second of birth (0-59)")
    gender: Gender = Field(..., description="Gender of the person")
    place: str = Field(..., description="Birth place name")
    lat: float = Field(..., ge=-90, le=90, description="Latitude of birth place")
    lon: float = Field(..., ge=-180, le=180, description="Longitude of birth place")
    tzone: float = Field(..., description="Timezone offset in hours")

    @field_validator("day")
    @classmethod
    def validate_day(cls, v, info):
        """Validate day based on month and year"""
        month = info.data.get("month")
        year = info.data.get("year")
        if month and year:
            import calendar

            _, last_day = calendar.monthrange(year, month)
            if v > last_day:
                raise ValueError(f"Day {v} is invalid for month {month} in year {year}")
        return v

    @field_validator("month")
    @classmethod
    def validate_month(cls, v):
        """Validate month range"""
        if v < 1 or v > 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        """Validate year range"""
        if v < 1900 or v > 2100:
            raise ValueError("Year must be between 100 and 2500")
        return v

    @field_validator("hour")
    @classmethod
    def validate_hour(cls, v):
        """Validate hour range"""
        if v < 0 or v > 23:
            raise ValueError("Hour must be between 0 and 23")
        return v

    @field_validator("min")
    @classmethod
    def validate_minute(cls, v):
        """Validate minute range"""
        if v < 0 or v > 59:
            raise ValueError("Minute must be between 0 and 59")
        return v

    @field_validator("sec")
    @classmethod
    def validate_second(cls, v):
        """Validate second range"""
        if v < 0 or v > 59:
            raise ValueError("Second must be between 0 and 59")
        return v

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("tzone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone offset"""
        if v < -14 or v > 14:
            raise ValueError("Timezone offset must be between -14 and 14 hours")
        return v


class DivineAPIClientV2:
    """
    Asynchronous v2 client for Divine API that uses httpx for optimal performance.
    Supports selective API invocation and resilient error handling.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.auth_token = settings.apis.divine_access_token or ""
        self.api_key = settings.apis.divine_api_key or ""
        # Bypass TLS cert verification if env not set to truthy (default: bypass for unstable envs/tests)
        self._verify_tls = False  # Simplified for now, can be made configurable later

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

    def _add_credentials(self, user_data: Dict) -> Dict:
        """Add API credentials to the request payload"""
        payload = user_data.copy()
        payload["api_key"] = self.api_key
        return payload

    async def _post_json(
        self, session: httpx.AsyncClient, url: str, payload: Dict
    ) -> Optional[Dict]:
        """Make async POST request with JSON payload"""
        try:
            # Add API credentials to payload
            payload_with_creds = self._add_credentials(payload)
            response = await session.post(
                url,
                json=payload_with_creds,
                headers=self._headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling {url}: {e}")
            return None

    async def _post_form(
        self, session: httpx.AsyncClient, url: str, payload: Dict
    ) -> Optional[Dict]:
        """Make async POST request with form data payload"""
        try:
            # Add API credentials to payload
            payload_with_creds = self._add_credentials(payload)
            response = await session.post(
                url,
                data=payload_with_creds,
                headers=self._headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()

            # Only treat as error if API explicitly returns success != 1
            if result.get("success") != 1:
                print(f"API Error for {url}: {result.get('msg', 'Unknown error')}")
                return None

            # Return the data portion if success = 1
            return result.get("data", result)
        except Exception as e:
            print(f"Error calling {url}: {e}")
            return None

    async def _fetch_basic_astro_details(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[BasicAstroDetailsResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v3/basic-astro-details"
        data = await self._post_form(session, url, user_data)
        return BasicAstroDetailsResponse(**data) if data else None

    async def _fetch_planetary_positions(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[PlanetaryPositionsResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/planetary-positions"
        data = await self._post_form(session, url, user_data)
        return PlanetaryPositionsResponse(**data) if data else None

    async def _fetch_composite_friendship(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[CompositeFriendshipResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/composite-friendship"
        data = await self._post_form(session, url, user_data)
        return CompositeFriendshipResponse(**data) if data else None

    async def _fetch_horoscope_chart(
        self,
        session: httpx.AsyncClient,
        user_data: Dict,
        chart_id: str = "D1",
        chart_style: str = "south",
    ) -> Optional[HoroscopeChartResponse]:
        url = (
            f"https://astroapi-3.divineapi.com/indian-api/v1/horoscope-chart/{chart_id}"
        )
        payload = user_data.copy()
        payload["chart_type"] = chart_style
        data = await self._post_form(session, url, payload)
        return HoroscopeChartResponse(**data) if data else None

    async def _fetch_vimshottari_dasha(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[VimshottariDashaResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha"
        payload = user_data.copy()
        payload["dasha_type"] = "antar-dasha"
        data = await self._post_form(session, url, payload)
        return VimshottariDashaResponse(**data) if data else None

    async def _fetch_sadhe_sati(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[SadheSatiResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/sadhe-sati"
        data = await self._post_form(session, url, user_data)
        return SadheSatiResponse(**data) if data else None

    async def _fetch_kaal_sarpa_dosha(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[KaalSarpaDoshaResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/kaal-sarpa-yoga"
        data = await self._post_form(session, url, user_data)
        return KaalSarpaDoshaResponse(**data) if data else None

    async def _fetch_manglik_dosha(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[ManglikDoshaResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/manglik-dosha"
        data = await self._post_form(session, url, user_data)
        return ManglikDoshaResponse(**data) if data else None

    async def _fetch_ascendant_report(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[AscendantReportResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/ascendant-report"
        data = await self._post_form(session, url, user_data)
        return AscendantReportResponse(**data) if data else None

    async def _fetch_shadbala(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[ShadbalaResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/shadbala"
        data = await self._post_form(session, url, user_data)
        return ShadbalaResponse(**data) if data else None

    async def _fetch_gemstone(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[GemstoneResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/gemstone-suggestion"
        data = await self._post_form(session, url, user_data)
        return GemstoneResponse(**data) if data else None

    async def _fetch_yogas(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[YogasResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/yogas"
        data = await self._post_form(session, url, user_data)
        return YogasResponse(**data) if data else None

    async def _fetch_planet_analysis(
        self, session: httpx.AsyncClient, user_data: Dict, planet: str
    ) -> Optional[PlanetAnalysisResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/planet-analysis"
        payload = user_data.copy()
        payload["analysis_planet"] = planet.lower()
        data = await self._post_form(session, url, payload)
        return PlanetAnalysisResponse(**data) if data else None

    async def _fetch_maha_dasha_analysis(
        self, session: httpx.AsyncClient, user_data: Dict, maha_dasha: str
    ) -> Optional[DashaAnalysisResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/maha-dasha-analysis"
        payload = user_data.copy()
        payload["maha_dasha"] = maha_dasha.lower()
        data = await self._post_form(session, url, payload)
        return DashaAnalysisResponse(**data) if data else None

    async def _fetch_antar_dasha_analysis(
        self,
        session: httpx.AsyncClient,
        user_data: Dict,
        maha_dasha: str,
        antar_dasha: str,
    ) -> Optional[DashaAnalysisResponse]:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/antar-dasha-analysis"
        payload = user_data.copy()
        payload["maha_dasha"] = maha_dasha.lower()
        payload["antar_dasha"] = antar_dasha.lower()
        data = await self._post_form(session, url, payload)
        return DashaAnalysisResponse(**data) if data else None

    def _analyze_dasha_periods(
        self, vimshottari_data: VimshottariDashaResponse, dasha_analysis_years: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze vimshottari dasha data to identify current and future periods.

        Args:
            vimshottari_data: Vimshottari dasha response data
            dasha_analysis_years: Number of years to look ahead for future antar dashas (default: 2)

        Returns:
            Dict containing:
            - current_maha_dasha: tuple (planet_name, start_date, end_date) or None
            - current_antar_dasha: tuple (maha_planet, antar_planet, start_date, end_date) or None
            - future_antar_dashas: List of tuples (maha_planet, antar_planet, start_date, end_date)
        """
        if not vimshottari_data or not vimshottari_data.maha_dasha:
            return {}

        current_date = date.today()
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
                current_maha_dasha = (
                    maha_dasha_planet.value,
                    maha_dasha_start,
                    maha_dasha_end,
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
                            current_antar_dasha = (
                                maha_dasha_planet.value,
                                antar_planet.value,
                                antar_start,
                                antar_end,
                            )

                            # Add future antar dashas from this maha dasha (next {dasha_analysis_years} years)
                            future_limit = date(
                                current_date.year + dasha_analysis_years,
                                current_date.month,
                                current_date.day,
                            )

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

                                # Only include future antar dashas within {dasha_analysis_years} years
                                if (
                                    future_antar_data.start_time > current_date
                                    and future_antar_data.start_time <= future_limit
                                ):
                                    future_antar_dashas.append(
                                        (
                                            maha_dasha_planet.value,
                                            future_antar_planet.value,
                                            future_antar_data.start_time,
                                            future_antar_data.end_time,
                                        )
                                    )
                            break

                    # If no current antar dasha found, look for future ones
                    if not current_antar_dasha:
                        future_limit = date(
                            current_date.year + dasha_analysis_years,
                            current_date.month,
                            current_date.day,
                        )

                        for (
                            antar_planet,
                            antar_data,
                        ) in maha_dasha_data.antar_dasha.items():
                            if (
                                not antar_data
                                or not antar_data.start_time
                                or not antar_data.end_time
                            ):
                                continue

                            # Include future antar dashas within {dasha_analysis_years} years
                            if (
                                antar_data.start_time > current_date
                                and antar_data.start_time <= future_limit
                            ):
                                future_antar_dashas.append(
                                    (
                                        maha_dasha_planet.value,
                                        antar_planet.value,
                                        antar_data.start_time,
                                        antar_data.end_time,
                                    )
                                )
                break

            # If this maha dasha is in the future, check for future antar dashas
            elif maha_dasha_start > current_date:
                future_limit = date(
                    current_date.year + dasha_analysis_years,
                    current_date.month,
                    current_date.day,
                )

                if maha_dasha_start <= future_limit and maha_dasha_data.antar_dasha:
                    for antar_planet, antar_data in maha_dasha_data.antar_dasha.items():
                        if (
                            not antar_data
                            or not antar_data.start_time
                            or not antar_data.end_time
                        ):
                            continue

                        # Include future antar dashas within {dasha_analysis_years} years
                        if (
                            antar_data.start_time > current_date
                            and antar_data.start_time <= future_limit
                        ):
                            future_antar_dashas.append(
                                (
                                    maha_dasha_planet.value,
                                    antar_planet.value,
                                    antar_data.start_time,
                                    antar_data.end_time,
                                )
                            )

        # Sort future antar dashas by start date
        future_antar_dashas.sort(key=lambda x: x[2])

        return {
            "current_maha_dasha": current_maha_dasha,
            "current_antar_dasha": current_antar_dasha,
            "future_antar_dashas": future_antar_dashas,
        }

    async def _fetch_dasha_analysis(
        self,
        session: httpx.AsyncClient,
        user_data: Dict,
        vimshottari_data: Optional[VimshottariDashaResponse],
        dasha_analysis_years: int,
    ) -> Optional[List[EnhancedDashaAnalysis]]:
        """
        Fetch comprehensive dasha analysis including current and future periods.
        """
        if not vimshottari_data:
            return None

        dasha_analysis = []

        # Analyze dasha periods
        dasha_periods = self._analyze_dasha_periods(
            vimshottari_data, dasha_analysis_years
        )

        if not dasha_periods:
            return None

        # Fetch maha dasha analysis for current period
        current_maha = dasha_periods.get("current_maha_dasha")
        if current_maha:
            maha_planet, maha_start, maha_end = current_maha
            maha_analysis = await self._fetch_maha_dasha_analysis(
                session, user_data, maha_planet
            )
            if maha_analysis:
                dasha_analysis.append(
                    EnhancedDashaAnalysis(
                        analysis_type="maha",
                        maha_planet=PlanetName(maha_planet),
                        antar_planet=None,
                        from_date=maha_start,
                        to_date=maha_end,
                        analysis=maha_analysis,
                    )
                )

        # Fetch antar dasha analysis for current period
        current_antar = dasha_periods.get("current_antar_dasha")
        if current_antar:
            maha_planet, antar_planet, antar_start, antar_end = current_antar
            antar_analysis = await self._fetch_antar_dasha_analysis(
                session, user_data, maha_planet, antar_planet
            )
            if antar_analysis:
                dasha_analysis.append(
                    EnhancedDashaAnalysis(
                        analysis_type="antar",
                        maha_planet=PlanetName(maha_planet),
                        antar_planet=PlanetName(antar_planet),
                        from_date=antar_start,
                        to_date=antar_end,
                        analysis=antar_analysis,
                    )
                )

        # Fetch antar dasha analysis for future periods (next {config.dasha_analysis_years} years)
        future_periods = dasha_periods.get("future_antar_dashas", [])
        for maha_dasha, antar_dasha, start_date, end_date in future_periods:
            antar_analysis = await self._fetch_antar_dasha_analysis(
                session, user_data, maha_dasha, antar_dasha
            )
            if antar_analysis:
                dasha_analysis.append(
                    EnhancedDashaAnalysis(
                        analysis_type="antar",
                        maha_planet=PlanetName(maha_dasha),
                        antar_planet=PlanetName(antar_dasha),
                        from_date=start_date,
                        to_date=end_date,
                        analysis=antar_analysis,
                    )
                )

        return dasha_analysis if dasha_analysis else None

    async def _fetch_all_planet_analysis(
        self, session: httpx.AsyncClient, user_data: Dict
    ) -> Optional[Dict[PlanetName, PlanetAnalysisResponse]]:
        """
        Fetch planet analysis for all planets in the PlanetName enum.
        """
        planet_analysis = {}

        for planet in PlanetName:
            analysis = await self._fetch_planet_analysis(
                session, user_data, planet.value
            )
            if analysis:
                planet_analysis[planet] = analysis

        return planet_analysis if planet_analysis else None

    async def fetch_all_astro_data(
        self, user_profile: UserProfile, config: Optional[APIConfig] = None
    ) -> RawAstroAPIData:
        """
        Main orchestrator method that fetches all enabled API data asynchronously.

        Args:
            user_profile: UserProfile object with validated birth data
            config: Configuration object specifying which APIs to call

        Returns:
            RawAstroAPIData: Consolidated response with all fetched data
        """
        if config is None:
            config = APIConfig()  # Use all defaults

        # Convert UserProfile to dict format expected by API methods
        user_data = {
            "full_name": user_profile.full_name,
            "day": user_profile.day,
            "month": user_profile.month,
            "year": user_profile.year,
            "hour": user_profile.hour,
            "min": user_profile.min,
            "sec": user_profile.sec,
            "gender": user_profile.gender.value.lower(),
            "place": user_profile.place,
            "lat": user_profile.lat,
            "lon": user_profile.lon,
            "tzone": user_profile.tzone,
        }

        # Create httpx session for this batch of API calls
        async with httpx.AsyncClient(verify=self._verify_tls) as session:
            # Prepare lists to hold async tasks
            tasks = []
            task_names = []

            # Core data APIs
            if config.basic_details:
                tasks.append(self._fetch_basic_astro_details(session, user_data))
                task_names.append("basic_details")

            if config.planetary_positions:
                tasks.append(self._fetch_planetary_positions(session, user_data))
                task_names.append("planetary_positions")

            if config.ascendant_report:
                tasks.append(self._fetch_ascendant_report(session, user_data))
                task_names.append("ascendant_report")

            if config.composite_friendship:
                tasks.append(self._fetch_composite_friendship(session, user_data))
                task_names.append("composite_friendship")

            # Chart APIs
            chart_tasks = []
            chart_ids = []
            if config.charts:
                for chart_id in config.charts:
                    chart_tasks.append(
                        self._fetch_horoscope_chart(
                            session, user_data, chart_id, config.chart_style
                        )
                    )
                    chart_ids.append(chart_id)

            # Dasha system APIs
            if config.vimshottari_dasha:
                tasks.append(self._fetch_vimshottari_dasha(session, user_data))
                task_names.append("vimshottari_dasha")

            if config.sadhe_sati:
                tasks.append(self._fetch_sadhe_sati(session, user_data))
                task_names.append("sadhe_sati")

            if config.kaal_sarpa_dosha:
                tasks.append(self._fetch_kaal_sarpa_dosha(session, user_data))
                task_names.append("kaal_sarpa_dosha")

            if config.manglik_dosha:
                tasks.append(self._fetch_manglik_dosha(session, user_data))
                task_names.append("manglik_dosha")

            if config.yogas:
                tasks.append(self._fetch_yogas(session, user_data))
                task_names.append("yogas")

            if config.gemstone:
                tasks.append(self._fetch_gemstone(session, user_data))
                task_names.append("gemstone")

            if config.shadbala:
                tasks.append(self._fetch_shadbala(session, user_data))
                task_names.append("shadbala")

            # Execute all tasks concurrently
            all_tasks = tasks + chart_tasks
            all_task_names = task_names + [f"chart_{cid}" for cid in chart_ids]

            # Execute all tasks concurrently
            results = await asyncio.gather(*all_tasks, return_exceptions=True)

            # Process results and build RawAstroAPIData
            result_dict = {}
            for i, (task_name, result) in enumerate(zip(all_task_names, results)):
                if isinstance(result, Exception):
                    print(f"Task {task_name} failed with exception: {result}")
                    result_dict[task_name] = None
                else:
                    result_dict[task_name] = result

            # Build horoscope_charts dict
            horoscope_charts = {}
            for i, chart_id in enumerate(chart_ids):
                chart_result = result_dict.get(f"chart_{chart_id}")
                if chart_result:
                    horoscope_charts[chart_id] = chart_result

            # Fetch dasha analysis if enabled and vimshottari data is available
            dasha_analysis = None
            if config.dasha_analysis and result_dict.get("vimshottari_dasha"):
                dasha_analysis = await self._fetch_dasha_analysis(
                    session,
                    user_data,
                    result_dict.get("vimshottari_dasha"),
                    config.dasha_analysis_years,
                )

            # Fetch planet analysis if enabled
            planet_analysis = None
            if config.planet_analysis:
                planet_analysis = await self._fetch_all_planet_analysis(
                    session, user_data
                )

            # Create and return RawAstroAPIData
            # Ensure required fields are present
            basic_details = result_dict.get("basic_details")
            planetary_pos = result_dict.get("planetary_positions")
            ascendant_rep = result_dict.get("ascendant_report")

            if not basic_details or not planetary_pos or not ascendant_rep:
                raise ValueError(
                    "Required astrological data is missing: basic_details, planetary_positions, or ascendant_report"
                )

            return RawAstroAPIData(
                basic_astro_details=basic_details,
                planetary_positions=planetary_pos,
                horoscope_charts=horoscope_charts if horoscope_charts else None,
                composite_friendship=result_dict.get("composite_friendship"),
                vimshottari_dasha=result_dict.get("vimshottari_dasha"),
                dasha_analysis=dasha_analysis,
                sadhe_sati=result_dict.get("sadhe_sati"),
                kaal_sarpa_dosha=result_dict.get("kaal_sarpa_dosha"),
                manglik_dosha=result_dict.get("manglik_dosha"),
                ascendant_report=ascendant_rep,
                yogas=result_dict.get("yogas"),
                shadbala=result_dict.get("shadbala"),
                planet_analysis=planet_analysis,
                gemstone=result_dict.get("gemstone"),
            )
