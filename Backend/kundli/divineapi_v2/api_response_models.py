from ast import Str
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class ZodiacSign(CaseInsensitiveEnum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


class Gender(CaseInsensitiveEnum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class LanguageEnum(CaseInsensitiveEnum):
    EN = "en"
    HI = "hi"


class PlanetName(CaseInsensitiveEnum):
    Sun = "Sun"
    Moon = "Moon"
    Mars = "Mars"
    Mercury = "Mercury"
    Jupiter = "Jupiter"
    Venus = "Venus"
    Saturn = "Saturn"
    Rahu = "Rahu"
    Ketu = "Ketu"
    Ascendant = "Ascendant"
    Uranus = "Uranus"
    Neptune = "Neptune"
    Pluto = "Pluto"


class Weekday(CaseInsensitiveEnum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"
    Sunday = "Sunday"


class PlanetaryFriendship(CaseInsensitiveEnum):
    BLANK = "-"
    FRIEND = "Friend"
    BEST_FRIEND = "Best Friend"
    NEUTRAL = "Neutral"
    ENEMY = "Enemy"
    BITTER_ENEMY = "Bitter Enemy"


class PayaModel(BaseModel):
    type: Optional[str] = None
    result: Optional[str] = None


# Basic Astro Details
class BasicAstroDetailsResponse(BaseModel):
    full_name: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    gender: Optional[Gender] = None
    place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[float] = None
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    tithi: Optional[str] = None
    paksha: Optional[str] = None
    paya: Optional[PayaModel] = None
    sunsign: Optional[ZodiacSign] = None
    moonsign: Optional[ZodiacSign] = None
    rashi_akshar: Optional[str] = None
    chandramasa: Optional[str] = None
    tatva: Optional[str] = None
    prahar: Optional[int] = None
    nakshatra: Optional[str] = None
    vaar: Optional[Weekday] = None
    varna: Optional[str] = None
    vashya: Optional[str] = None
    yoni: Optional[str] = None
    gana: Optional[str] = None
    nadi: Optional[str] = None
    yoga: Optional[str] = None
    karana: Optional[str] = None
    ayanamsha: Optional[str] = None
    yunja: Optional[str] = None

    @field_validator("sunrise", "sunset", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # raise ValueError(f"Invalid datetime format: {value}")
                pass  # pass through for Pydantic to handle
        return value


# Planetary Positions
class PlanetModel(BaseModel):
    name: Optional[PlanetName] = None
    name_lan: Optional[str] = None
    full_degree: Optional[float] = None
    speed: Optional[float] = None
    is_retro: Optional[bool] = None
    is_combusted: Optional[bool] = None
    longitude: Optional[str] = None
    sign: Optional[ZodiacSign] = None
    sign_no: Optional[int] = None
    rashi_lord: Optional[PlanetName] = None
    nakshatra: Optional[str] = None
    nakshatra_pada: Optional[int] = None
    nakshatra_no: Optional[int] = None
    nakshatra_lord: Optional[PlanetName] = None
    sub_lord: Optional[PlanetName] = None
    awastha: Optional[str] = None
    karakamsha: Optional[str] = None
    house: Optional[int] = None
    type: Optional[str] = None
    lord_of: Optional[str] = None
    image: Optional[str] = None


class PlanetaryPositionsResponse(BaseModel):
    date: Optional[dt_date] = None
    time: Optional[dt_time] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[float] = None
    planets: List[PlanetModel] = []


# Composite Friendship
class PlanetFriendshipSubModel(BaseModel):
    Sun: Optional[PlanetaryFriendship] = None
    Moon: Optional[PlanetaryFriendship] = None
    Mars: Optional[PlanetaryFriendship] = None
    Mercury: Optional[PlanetaryFriendship] = None
    Jupiter: Optional[PlanetaryFriendship] = None
    Venus: Optional[PlanetaryFriendship] = None
    Saturn: Optional[PlanetaryFriendship] = None


class PlanetFriendshipModel(BaseModel):
    Sun: Optional[PlanetFriendshipSubModel] = None
    Moon: Optional[PlanetFriendshipSubModel] = None
    Mars: Optional[PlanetFriendshipSubModel] = None
    Mercury: Optional[PlanetFriendshipSubModel] = None
    Jupiter: Optional[PlanetFriendshipSubModel] = None
    Venus: Optional[PlanetFriendshipSubModel] = None
    Saturn: Optional[PlanetFriendshipSubModel] = None


class CompositeFriendshipResponse(BaseModel):
    natural_friendship: Optional[PlanetFriendshipModel] = None
    temporary_friendship: Optional[PlanetFriendshipModel] = None
    five_fold_friendship: Optional[PlanetFriendshipModel] = None


# Horoscope Charts
class PlanetSymbolModel(BaseModel):
    name: Optional[PlanetName] = None
    symbol: Optional[str] = None


class HouseModel(BaseModel):
    sign_no: int = Field(..., ge=1, le=12)
    planet: Optional[List[PlanetSymbolModel]] = Field(default_factory=list)


class HoroscopeChartResponse(BaseModel):
    svg: Optional[str] = None
    data: Optional[Dict[str, HouseModel]] = None
    base64_image: Optional[str] = None


# Vimshottari Dasha
class DashaPeriod(BaseModel):
    start_time: Optional[dt_date] = None
    end_time: Optional[dt_date] = None

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_date_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Handle invalid date strings like '--', 'N/A', etc.
            if v.strip() in ["--", "-", "NA", "", " ", "null", "undefined"]:
                return None
            try:
                # Try to parse the date string
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                # Try to normalize the date string to handle single digit month/day
                try:
                    # Split by '-' and ensure proper formatting
                    parts = v.split("-")
                    if len(parts) == 3:
                        year, month, day = parts
                        # Ensure month and day have leading zeros if needed
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        return datetime.strptime(normalized_date, "%Y-%m-%d").date()
                except (ValueError, AttributeError):
                    pass
                # If all attempts fail, return None instead of raising an error
                return None
        return v


class MahaDasha(BaseModel):
    start_date: Optional[dt_date] = None
    end_date: Optional[dt_date] = None
    antar_dasha: Optional[Dict[PlanetName, DashaPeriod]] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Handle invalid date strings like '--', 'N/A', etc.
            if v.strip() in ["--", "-", "NA", "", " ", "null", "undefined"]:
                return None
            try:
                # Try to parse the date string
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                # Try to normalize the date string to handle single digit month/day
                try:
                    # Split by '-' and ensure proper formatting
                    parts = v.split("-")
                    if len(parts) == 3:
                        year, month, day = parts
                        # Ensure month and day have leading zeros if needed
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        return datetime.strptime(normalized_date, "%Y-%m-%d").date()
                except (ValueError, AttributeError):
                    pass
                # If all attempts fail, return None instead of raising an error
                return None
        return v


class VimshottariDashaResponse(BaseModel):
    date: Optional[dt_date] = None
    time: Optional[dt_time] = None
    maha_dasha: Optional[Dict[PlanetName, MahaDasha]] = None

    @field_validator("date", "time", mode="before")
    @classmethod
    def validate_date_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Handle invalid date strings like '--', 'N/A', etc.
            if v.strip() in ["--", "-", "NA", "", " ", "null", "undefined"]:
                return None
            try:
                # Try to parse the date string with standard format (YYYY-MM-DD)
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                # Try to normalize the date string to handle single digit month/day
                try:
                    # Split by '-' and ensure proper formatting
                    parts = v.split("-")
                    if len(parts) == 3:
                        year, month, day = parts
                        # Ensure month and day have leading zeros if needed
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        return datetime.strptime(normalized_date, "%Y-%m-%d").date()
                except (ValueError, AttributeError):
                    pass
                # If all attempts fail, return None instead of raising an error
                return None
        return v


# Vimshottari Dasha Analysis
class DashAnalysisModel(BaseModel):
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None


class DashaAnalysisResponse(BaseModel):
    maha_dasha: Optional[PlanetName] = None
    antar_dasha: Optional[PlanetName] = None
    pratyantar_dasha: Optional[PlanetName] = None
    analysis: Optional[DashAnalysisModel] = None


# Sadhe Sati
class SadheSatiResult(BaseModel):
    result: Optional[bool] = None
    consideration_date: Optional[dt_date] = None
    saturn_sign: Optional[ZodiacSign] = None
    saturn_retrograde: Optional[bool] = None


class SadheSatiPhaseModel(BaseModel):
    sign_symbol: Optional[str] = None
    sign_name: Optional[ZodiacSign] = None
    is_retro: Optional[bool] = None
    phase: Optional[str] = None
    date: Optional[dt_date] = None


class SadheSatiResponse(BaseModel):
    sadhesati: Optional[SadheSatiResult] = None
    sadhesati_life_analysis: Optional[List[SadheSatiPhaseModel]] = None
    small_panoti: Optional[List[SadheSatiPhaseModel]] = None
    moon_sign: Optional[ZodiacSign] = None
    remedies: Optional[List[str]] = None


# Kaal Sarpa Dosha
class KaalSarpaDoshaResponse(BaseModel):
    result: Optional[bool] = None
    intensity: Optional[str] = None
    name: Optional[str] = None
    direction: Optional[str] = None
    remedies: Optional[List[str]] = None


# Manglik Dosha
class ManglikDoshaResponse(BaseModel):
    manglik_dosha: Optional[str] = None
    strength: Optional[str] = None
    percentage: Optional[float] = None
    remedies: Optional[List[str]] = None
    comment: Optional[List[str]] = None


# Shadbala
class PlanetaryBala(BaseModel):
    Sun: Optional[float] = None
    Moon: Optional[float] = None
    Mars: Optional[float] = None
    Mercury: Optional[float] = None
    Jupiter: Optional[float] = None
    Venus: Optional[float] = None
    Saturn: Optional[float] = None


class SthanaBala(BaseModel):
    uccha_bala: Optional[PlanetaryBala] = None
    saptavarghiya_bala: Optional[PlanetaryBala] = None
    yugmayugma_bhamsha_bala: Optional[PlanetaryBala] = None
    kendradi_bala: Optional[PlanetaryBala] = None
    drekkana_bala: Optional[PlanetaryBala] = None
    total: Optional[PlanetaryBala] = None


class KaalBala(BaseModel):
    nattunnata_bala: Optional[PlanetaryBala] = None
    paksha_bala: Optional[PlanetaryBala] = None
    tribhaga_bala: Optional[PlanetaryBala] = None
    varshadhipati: Optional[PlanetaryBala] = None
    maasadipati: Optional[PlanetaryBala] = None
    vaaradhipati: Optional[PlanetaryBala] = None
    horadhipati: Optional[PlanetaryBala] = None
    ayana_bala: Optional[PlanetaryBala] = None
    yuddha_bala: Optional[PlanetaryBala] = None
    total: Optional[PlanetaryBala] = None


class ShadbalaResponse(BaseModel):
    sthana_bala: Optional[SthanaBala] = None
    digbala: Optional[PlanetaryBala] = None
    kaal_bala: Optional[KaalBala] = None
    naisargika_bala: Optional[PlanetaryBala] = None
    chestha_bala: Optional[PlanetaryBala] = None
    drik_bala: Optional[PlanetaryBala] = None
    total_shadbala: Optional[PlanetaryBala] = None
    shadbala_in_rupa: Optional[PlanetaryBala] = None
    min_require: Optional[PlanetaryBala] = None
    ratio: Optional[PlanetaryBala] = None
    rank: Optional[PlanetaryBala] = None


# Gemstone Suggestions
class GemstoneSet(BaseModel):
    Primary: Optional[str] = None
    Secondary: Optional[str] = None


class GemstoneDetails(BaseModel):
    gemstones: Optional[GemstoneSet] = None
    day_to_wear: Optional[str] = None
    finger_to_wear: Optional[str] = None
    time_to_wear: Optional[str] = None
    mantra: Optional[str] = None


class GemstoneResponse(BaseModel):
    lucky_stone: Optional[GemstoneDetails] = None
    life_stone: Optional[GemstoneDetails] = None
    dasha_stone: Optional[List[Any]] = None


# Ascendant Report
class AscendantAnalysisModel(BaseModel):
    personality: Optional[str] = None
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None


class AscendantReportResponse(BaseModel):
    planetary_lord: Optional[PlanetName] = None
    symble: Optional[str] = None
    characteristics: Optional[str] = None
    day_of_fast: Optional[Weekday] = None
    lucky_stone: Optional[List[str]] = None
    ascendant: Optional[ZodiacSign] = None
    image: Optional[str] = None
    analysis: Optional[AscendantAnalysisModel] = None


# Yogas
class YogaDetailsContentModel(BaseModel):
    detail: List[str] = []
    remedies: Optional[List[str]] = None


class YogaDetailsModel(BaseModel):
    name: Optional[str] = None
    is_valid: Optional[bool] = None
    content: Optional[YogaDetailsContentModel] = None


class PanchaMahapurushaYoga(BaseModel):
    bhadra_pancha_mahapurusha_yoga: Optional[YogaDetailsModel] = None
    malavya_pancha_mahapurusha_yoga: Optional[YogaDetailsModel] = None
    ruchaka_pancha_mahapurusha_yoga: Optional[YogaDetailsModel] = None
    hamsa_pancha_mahapurusha_yoga: Optional[YogaDetailsModel] = None
    sasha_pancha_mahapurusha_yoga: Optional[YogaDetailsModel] = None


class LunarYoga(BaseModel):
    sunapha_yoga: Optional[YogaDetailsModel] = None
    anapha_yoga: Optional[YogaDetailsModel] = None
    duradhara_yoga: Optional[YogaDetailsModel] = None


class SolarYoga(BaseModel):
    vesi_yoga: Optional[YogaDetailsModel] = None
    vasi_yoga: Optional[YogaDetailsModel] = None
    ubhayachari_yoga: Optional[YogaDetailsModel] = None


class TrimurtiYogas(BaseModel):
    hari_yoga: Optional[YogaDetailsModel] = None
    hara_yoga: Optional[YogaDetailsModel] = None
    brahma_yoga: Optional[YogaDetailsModel] = None


class YogasResponse(BaseModel):
    raj_yoga: Optional[YogaDetailsModel] = None
    vipreet_raj_yoga: Optional[YogaDetailsModel] = None
    dhan_yoga: Optional[YogaDetailsModel] = None
    buddha_aditya_yoga: Optional[YogaDetailsModel] = None
    gaja_kesari_yoga: Optional[YogaDetailsModel] = None
    amala_yoga: Optional[YogaDetailsModel] = None
    parvata_yoga: Optional[YogaDetailsModel] = None
    kahala_yoga: Optional[YogaDetailsModel] = None
    chamara_yoga: Optional[YogaDetailsModel] = None
    sankha_yoga: Optional[YogaDetailsModel] = None
    lagnadhi_yoga: Optional[YogaDetailsModel] = None
    chandradhi_yoga: Optional[YogaDetailsModel] = None
    pancha_mahapurusha_yoga: Optional[PanchaMahapurushaYoga] = None
    lunar_yoga: Optional[LunarYoga] = None
    solar_yoga: Optional[SolarYoga] = None
    shubh_kartari_yoga: Optional[YogaDetailsModel] = None
    paap_kartari_yoga: Optional[YogaDetailsModel] = None
    saraswati_yoga: Optional[YogaDetailsModel] = None
    lakshmi_yoga: Optional[YogaDetailsModel] = None
    kusuma_yoga: Optional[YogaDetailsModel] = None
    kalindi_yoga: Optional[YogaDetailsModel] = None
    kalpadruma_yoga: Optional[YogaDetailsModel] = None
    trimurti_yogas: Optional[TrimurtiYogas] = None
    khadga_yoga: Optional[YogaDetailsModel] = None
    koorma_yoga: Optional[YogaDetailsModel] = None
    matsya_yoga: Optional[YogaDetailsModel] = None
    sarada_yoga: Optional[YogaDetailsModel] = None
    srinatha_yoga: Optional[YogaDetailsModel] = None
    mridanga_yoga: Optional[YogaDetailsModel] = None
    bheri_yoga: Optional[YogaDetailsModel] = None


# Planet Analysis
class PlanetAnalysisItem(BaseModel):
    heading: str
    description: str


class PlanetAnalysis(BaseModel):
    planet_in_house: Optional[List[PlanetAnalysisItem]] = None
    planet_in_sign: Optional[List[PlanetAnalysisItem]] = None


class PlanetAnalysisResponse(BaseModel):
    planet: Optional[PlanetName] = None
    sign: Optional[ZodiacSign] = None
    sign_no: Optional[int] = None
    house: Optional[int] = None
    longitude: Optional[str] = None
    lord: Optional[PlanetName] = None
    image: Optional[str] = None
    analysis: Optional[PlanetAnalysis] = None


### =================================================================================
###
### =================================================================================

# Put the models we actively use above this block, and the unused models below this block

### =================================================================================
###
### =================================================================================


# Sub Planet Positions
class SubPlanetModel(BaseModel):
    name: Optional[str] = None
    name_lan: Optional[str] = None
    full_degree: Optional[str] = None
    longitude: Optional[str] = None
    sign: Optional[str] = None
    sign_no: Optional[int] = None
    sign_name: Optional[str] = None
    house: Optional[int] = None
    nakshatra: Optional[str] = None
    nakshatra_pada: Optional[int] = None
    nakshatra_no: Optional[int] = None
    nakshatra_lord: Optional[str] = None
    rashi_lord: Optional[str] = None
    sub_lord: Optional[str] = None
    sub_sub_lord: Optional[str] = None


class SubPlanetPositionsResponse(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    timezone: Optional[str] = None
    planets: Optional[List[SubPlanetModel]] = None


class SubPlanetChartSignModel(BaseModel):
    sign_no: Optional[int] = None
    planet: Optional[List[PlanetSymbolModel]] = None


class SubPlanetChartResponse(BaseModel):
    svg: Optional[str] = None
    base64_image: Optional[str] = None
    data: Optional[Dict[str, SubPlanetChartSignModel]] = None


# KP Planetary Positions
class KPPlanetModel(BaseModel):
    name: Optional[str] = None
    full_degree: Optional[str] = None
    speed: Optional[str] = None
    is_retro: Optional[str] = None
    is_combusted: Optional[str] = None
    longitude: Optional[str] = None
    sign: Optional[str] = None
    sign_no: Optional[int] = None
    rashi_lord: Optional[str] = None
    nakshatra: Optional[str] = None
    nakshatra_pada: Optional[int] = None
    nakshatra_no: Optional[int] = None
    nakshatra_lord: Optional[str] = None
    sub_lord: Optional[str] = None
    sub_sub_lord: Optional[str] = None
    house: Optional[int] = None


class KPPlanetaryPositionsResponse(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    timezone: Optional[str] = None
    planets: Optional[List[KPPlanetModel]] = None


# KP Cuspal
class HouseCuspModel(BaseModel):
    sign: Optional[str] = None
    degree: Optional[str] = None


class CuspTableSignModel(BaseModel):
    cusp: Optional[int] = None
    house_cusp: Optional[HouseCuspModel] = None
    rashi_lord: Optional[str] = None
    nakshatra: Optional[str] = None
    nakshatra_pada: Optional[int] = None
    nakshatra_no: Optional[int] = None
    nakshatra_lord: Optional[str] = None
    sub_lord: Optional[str] = None
    sub_sub_lord: Optional[str] = None


class KPCuspalResponse(BaseModel):
    svg: Optional[str] = None
    table_data: Optional[Dict[str, CuspTableSignModel]] = None
    data: Optional[Dict[str, SubPlanetChartSignModel]] = None


# KP Astrology
class KPChartRequest(BaseModel):
    api_key: Optional[str] = None
    full_name: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    hour: Optional[str] = None
    min: Optional[str] = None
    sec: Optional[str] = None
    gender: Optional[str] = None
    place: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    tzone: Optional[str] = None
    lan: Optional[str] = None


class KPChartData(BaseModel):
    table: Optional[str] = None


class KPChartResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[KPChartData] = None


# Bhava Kundli
class BhavaKundliRequest(BaseModel):
    api_key: Optional[str] = None
    full_name: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    hour: Optional[str] = None
    min: Optional[str] = None
    sec: Optional[str] = None
    gender: Optional[str] = None
    place: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    tzone: Optional[str] = None
    lan: Optional[str] = None


class BhavaTableEntry(BaseModel):
    house_no: Optional[int] = None
    sign: Optional[str] = None
    degree: Optional[str] = None
    lord: Optional[str] = None
    nakshatra: Optional[str] = None


class BhavaKundliData(BaseModel):
    table: Optional[list[BhavaTableEntry]] = None


class BhavaKundliResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[BhavaKundliData] = None


# Yogini Dasha
class YoginiDashaRequest(BaseModel):
    api_key: Optional[str] = None
    full_name: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    hour: Optional[str] = None
    minute: Optional[str] = None
    meridian: Optional[str] = None
    gender: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    timezone: Optional[str] = None


class YoginiDashaResponse(BaseModel):
    status: Optional[str] = None
    data: Any = None


# Kaal Chakra Dasha
class KaalChakraRequest(BaseModel):
    api_key: Optional[str] = None
    full_name: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    hour: Optional[str] = None
    minute: Optional[str] = None
    meridian: Optional[str] = None
    gender: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    timezone: Optional[str] = None


class KaalChakraResponse(BaseModel):
    status: Optional[str] = None
    data: Any = None


# Sudarshana Chakra
class SudarshanaRequest(BaseModel):
    api_key: Optional[str] = None
    full_name: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    hour: Optional[str] = None
    minute: Optional[str] = None
    meridian: Optional[str] = None
    gender: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    timezone: Optional[str] = None


class SudarshanaResponse(BaseModel):
    status: Optional[str] = None
    data: Optional[dict] = None


# Ghata Chakra
class GhataChakraResponse(BaseModel):
    moon_sign: Optional[str] = None
    month: Optional[str] = None
    tithi: Optional[str] = None
    vaar: Optional[str] = None
    nakshatra: Optional[str] = None
    yoga: Optional[str] = None
    karana: Optional[str] = None


# Bhinnashtakavarga
class AshtakavargaRequest(BaseModel):
    full_name: str = Field(..., example="Rahul Kumar")
    day: int = Field(..., ge=1, le=31, example=24)
    month: int = Field(..., ge=1, le=12, example=5)
    year: int = Field(..., ge=1900, example=1995)
    hour: int = Field(..., ge=0, le=23, example=14)
    min: int = Field(..., ge=0, le=59, example=40)
    sec: int = Field(..., ge=0, le=59, example=43)
    gender: Literal["male", "female"] = Field(..., example="male")
    place: str = Field(..., example="New Delhi")
    lat: float = Field(..., example=28.7041)
    lon: float = Field(..., example=77.1025)
    tzone: float = Field(..., example=5.5, description="Timezone offset from UTC")
    lan: Literal["en", "hi"] = Field("en", example="en", description="Language code")


class PlanetAshtakavargaData(BaseModel):
    """Individual planet's ashtakavarga data with points for each house"""

    # Houses 1-12 as string keys to match API response
    house_1: Optional[int] = Field(default=None, alias="1")
    house_2: Optional[int] = Field(default=None, alias="2")
    house_3: Optional[int] = Field(default=None, alias="3")
    house_4: Optional[int] = Field(default=None, alias="4")
    house_5: Optional[int] = Field(default=None, alias="5")
    house_6: Optional[int] = Field(default=None, alias="6")
    house_7: Optional[int] = Field(default=None, alias="7")
    house_8: Optional[int] = Field(default=None, alias="8")
    house_9: Optional[int] = Field(default=None, alias="9")
    house_10: Optional[int] = Field(default=None, alias="10")
    house_11: Optional[int] = Field(default=None, alias="11")
    house_12: Optional[int] = Field(default=None, alias="12")
    points: Optional[int] = None


class PlanetAshtakavargaTable(BaseModel):
    """Ashtakavarga table for a specific planet"""

    Saturn: Optional[PlanetAshtakavargaData] = None
    Jupiter: Optional[PlanetAshtakavargaData] = None
    Mars: Optional[PlanetAshtakavargaData] = None
    Sun: Optional[PlanetAshtakavargaData] = None
    Venus: Optional[PlanetAshtakavargaData] = None
    Mercury: Optional[PlanetAshtakavargaData] = None
    Moon: Optional[PlanetAshtakavargaData] = None
    Ascendant: Optional[PlanetAshtakavargaData] = None


class AshtakavargaChartData(BaseModel):
    """Chart data for a planet"""

    svg: Optional[str] = None


class AshtakavargaDataResponse(BaseModel):
    table: Optional[Dict[str, PlanetAshtakavargaTable]] = None
    chart: Optional[Dict[str, AshtakavargaChartData]] = None


class PlanetAshtakavarga(BaseModel):
    planet: str
    house_wise_points: Dict[str, int]  # e.g. {"House1": 4, "House2": 3, ...}
    total_points: int


class AshtakavargaResponse(BaseModel):
    success: int
    data: List[PlanetAshtakavarga]
    total_points: Dict[str, int]  # {"Sun": 25, "Moon": 28, ...}


# Kundli Transit
# TO be added
