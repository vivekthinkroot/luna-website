from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, Union, List, Dict
from enum import Enum 

class PayaModel(BaseModel):
    type: Optional[str] = None
    result: Optional[str] = None

class BasicAstroDetailsResponse(BaseModel):
    full_name: str | None = None
    year: str | None = None
    month: str | None = None
    day: str | None = None
    hour: str | None = None
    minute: str | None = None
    gender: str | None = None
    place: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    timezone: str | None = None
    sunrise: str | None = None
    sunset: str | None = None
    tithi: str | None = None
    paksha: str | None = None
    paya: PayaModel | None = None
    sunsign: str | None = None
    moonsign: str | None = None
    rashi_akshar: str | None = None
    chandramasa: str | None = None
    tatva: str | None = None
    prahar: int | None = None
    nakshatra: str | None = None
    vaar: str | None = None
    varna: str | None = None
    vashya: str | None = None
    yoni: str | None = None
    gana: str | None = None
    nadi: str | None = None
    yoga: str | None = None
    karana: str | None = None
    ayanamsha: str | None = None
    yUNja: str | None = Field(default=None, alias="yunja")

class PlanetModel(BaseModel):
    name: str | None = None
    sign: str | None = None
    image: Optional[str] = None

class PlanetaryPositionsResponse(BaseModel):
    date: str | None = None
    time: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    timezone: str | None = None
    planets: List[PlanetModel] = []

class AscendantAnalysisModel(BaseModel):
    personality: Optional[str] = None
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None

class AscendantReportResponse(BaseModel):
    planetary_lord: Optional[str] = None
    symble: Optional[str] = None
    characteristics: Optional[str] = None
    day_of_fast: Optional[str] = None
    lucky_stone: Optional[List[str]] = None
    ascendant: Optional[str] = None
    image: Optional[str] = None
    analysis: Optional[AscendantAnalysisModel] = None

class CompositeFriendshipResponse(BaseModel):
    natural_friendship: Optional[Dict[str, Dict[str, str]]] = None

class HoroscopeChartResponse(BaseModel):
    svg: Optional[str] = None
    data: Union[str, Dict[str, Any]] = None
    base64_image: Optional[str] = None

class DashaPeriod(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class MahaDasha(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    antar_dasha: Optional[Dict[str, DashaPeriod]] = None

class VimshottariDashaResponse(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    maha_dasha: Optional[Dict[str, MahaDasha]] = None

class SadheSatiResult(BaseModel):
    result: Optional[str] = None
    consideration_date: Optional[str] = None
    saturn_sign: Optional[str] = None
    saturn_retrograde: Optional[str] = None

class SadheSatiPhaseModel(BaseModel):
    sign_symbol: Optional[str] = None
    sign_name: Optional[str] = None
    is_retro: Optional[str] = None
    phase: Optional[str] = None
    date: Optional[str] = None

class SadheSatiResponse(BaseModel):
    sadhesati: Optional[SadheSatiResult] = None
    sadhesati_life_analysis: Optional[List[SadheSatiPhaseModel]] = None

class KaalSarpaDoshaResponse(BaseModel):
    result: Optional[str] = None
    intensity: Optional[str] = ""
    name: Optional[str] = ""
    direction: Optional[str] = ""
    remedies: Optional[List[str]] = None

class ManglikDoshaResponse(BaseModel):
    manglik_dosha: Optional[str] = None
    strength: Optional[str] = None
    percentage: Optional[float] = None
    remedies: Optional[List[str]] = None
    comment: Optional[List[str]] = None

class GhataChakraResponse(BaseModel):
    moon_sign: Optional[str] = None
    month: Optional[str] = None
    tithi: Optional[str] = None
    vaar: Optional[str] = None
    nakshatra: Optional[str] = None
    yoga: Optional[str] = None
    karana: Optional[str] = None

#to ckeck working from here
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

class PlanetSymbolModel(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None

class SubPlanetChartSignModel(BaseModel):
    sign_no: Optional[int] = None
    planet: Optional[List[PlanetSymbolModel]] = None

class SubPlanetChartResponse(BaseModel):
    svg: Optional[str] = None
    base64_image: Optional[str] = None
    data: Optional[Dict[str, SubPlanetChartSignModel]] = None

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

class MahaDashaRequest(BaseModel):
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

class MahaDashaPeriod(BaseModel):
    planet: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None

class MahaDashaData(BaseModel):
    maha_dasha: Optional[list[MahaDashaPeriod]] = None

class MahaDashaResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[MahaDashaData] = None

class AntarDashaRequest(MahaDashaRequest):
    pass

class AntarDashaPeriod(BaseModel):
    main_dasha_lord: str = Field(..., alias="mahadasha_lord")
    sub_dasha_lord: str = Field(..., alias="antardasha_lord")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None

class AntarDashaData(BaseModel):
    antar_dasha: Optional[list[AntarDashaPeriod]] = None

class AntarDashaResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[AntarDashaData] = None

class PratyantarDashaRequest(MahaDashaRequest):
    pass

class PratyantarDashaPeriod(BaseModel):
    main_dasha_lord: str = Field(..., alias="mahadasha_lord")
    sub_dasha_lord: str = Field(..., alias="antardasha_lord")
    sub_sub_dasha_lord: str = Field(..., alias="pratyantar_dasha_lord")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None

class PratyantarDashaData(BaseModel):
    pratyantar_dasha: Optional[list[PratyantarDashaPeriod]] = None

class PratyantarDashaResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[PratyantarDashaData] = None

class ShadbalaRequest(BaseModel):
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

class ShadbalaResponse(BaseModel):
    status: Optional[str] = None
    data: Any = None

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class LanguageEnum(str, Enum):
    en = "en"
    hi = "hi"

class GemstoneRequest(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full name of the person")
    day: int = Field(..., ge=1, le=31, description="Day of birth")
    month: int = Field(..., ge=1, le=12, description="Month of birth")
    year: int = Field(..., ge=1, description="Year of birth")
    hour: int = Field(..., ge=0, le=23, description="Hour of birth (24h format)")
    minute: int = Field(..., ge=0, le=59, description="Minute of birth")
    second: int = Field(..., ge=0, le=59, description="Second of birth")
    gender: GenderEnum = Field(..., description="Gender of the person")
    place: str = Field(..., min_length=1, description="Place of birth")
    lat: float = Field(..., ge=-90, le=90, description="Latitude of birth place")
    lon: float = Field(..., ge=-180, le=180, description="Longitude of birth place")
    tzone: float = Field(..., ge=-12, le=14, description="Timezone offset in hours")
    lan: LanguageEnum = Field(..., description="Language code (e.g., en, hi)")

    
class GemstoneSet(BaseModel):
    Primary: Optional[str] = None
    Secondary: Optional[str] = None

class GemstoneDetails(BaseModel):
    gemstones: Optional[GemstoneSet] = None
    day_to_wear: Optional[str] = None
    finger_to_wear: Optional[str] = None
    time_to_wear: Optional[str] = None
    mantra: Optional[str] = None

class GemstoneSuggestionData(BaseModel):
    lucky_stone: Optional[GemstoneDetails] = None
    life_stone: Optional[GemstoneDetails] = None
    dasha_stone: Optional[GemstoneDetails] = None

class GemstoneResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[GemstoneSuggestionData] = None

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

class YogasRequest(BaseModel):
    # api_key: Optional[str] = None
    # full_name: Optional[str] = None
    # day: Optional[str] = None
    # month: Optional[str] = None
    # year: Optional[str] = None
    # hour: Optional[str] = None
    # minute: Optional[str] = None
    # meridian: Optional[str] = None
    # gender: Optional[str] = None
    # lat: Optional[str] = None
    # lon: Optional[str] = None
    # timezone: Optional[str] = None
    api_key: str = Field(..., description="Your DivineAPI key")
    full_name: str
    day: int
    month: int
    year: int
    hour: int
    min: int
    sec: int
    gender: Literal["male", "female"]
    place: str
    lat: float
    lon: float
    tzone: float
    lan: Literal["en", "hi"] = "en"

class YogaContent(BaseModel):
    detail: List[str] = []
    remedies: Optional[List[str]] = None


class Yoga(BaseModel):
    name: Optional[str] = None
    is_valid: Optional[str] = None  # "true"/"false" (string, not bool)
    content: Optional[YogaContent] = None

class PanchaMahapurushaYoga(BaseModel):
    bhadra_pancha_mahapurusha_yoga: Optional[Yoga] = None
    malavya_pancha_mahapurusha_yoga: Optional[Yoga] = None
    ruchaka_pancha_mahapurusha_yoga: Optional[Yoga] = None
    hamsa_pancha_mahapurusha_yoga: Optional[Yoga] = None
    sasha_pancha_mahapurusha_yoga: Optional[Yoga] = None


class LunarYoga(BaseModel):
    sunapha_yoga: Optional[Yoga] = None
    anapha_yoga: Optional[Yoga] = None
    duradhara_yoga: Optional[Yoga] = None


class SolarYoga(BaseModel):
    vesi_yoga: Optional[Yoga] = None
    vasi_yoga: Optional[Yoga] = None
    ubhayachari_yoga: Optional[Yoga] = None


class TrimurtiYogas(BaseModel):
    hari_yoga: Optional[Yoga] = None
    hara_yoga: Optional[Yoga] = None
    brahma_yoga: Optional[Yoga] = None




class YogasData(BaseModel):
    raj_yoga: Optional[Yoga] = None
    vipreet_raj_yoga: Optional[Yoga] = None
    dhan_yoga: Optional[Yoga] = None
    buddha_aditya_yoga: Optional[Yoga] = None
    gaja_kesari_yoga: Optional[Yoga] = None
    amala_yoga: Optional[Yoga] = None
    parvata_yoga: Optional[Yoga] = None
    kahala_yoga: Optional[Yoga] = None
    chamara_yoga: Optional[Yoga] = None
    sankha_yoga: Optional[Yoga] = None
    lagnadhi_yoga: Optional[Yoga] = None
    chandradhi_yoga: Optional[Yoga] = None
    pancha_mahapurusha_yoga: Optional[PanchaMahapurushaYoga] = None
    lunar_yoga: Optional[LunarYoga] = None
    solar_yoga: Optional[SolarYoga] = None
    shubh_kartari_yoga: Optional[Yoga] = None
    paap_kartari_yoga: Optional[Yoga] = None
    saraswati_yoga: Optional[Yoga] = None
    lakshmi_yoga: Optional[Yoga] = None
    kusuma_yoga: Optional[Yoga] = None
    kalindi_yoga: Optional[Yoga] = None
    kalpadruma_yoga: Optional[Yoga] = None
    trimurti_yogas: Optional[TrimurtiYogas] = None
    khadga_yoga: Optional[Yoga] = None
    koorma_yoga: Optional[Yoga] = None
    matsya_yoga: Optional[Yoga] = None
    sarada_yoga: Optional[Yoga] = None
    srinatha_yoga: Optional[Yoga] = None
    mridanga_yoga: Optional[Yoga] = None
    bheri_yoga: Optional[Yoga] = None


class YogasResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[YogasData] = None

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

class PlanetAnalysisRequest(BaseModel):
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
    analysis_planet: Optional[str] = None

class PlanetAnalysisResponse(BaseModel):
    status: Optional[str] = None
    data: Any = None

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

class DashaAnalysisModel(BaseModel):
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None

class MahaDashaAnalysisContent(BaseModel):
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None


class MahaDashaAnalysisData(BaseModel):
    maha_dasha: Optional[str] = None
    analysis: Optional[MahaDashaAnalysisContent] = None

class MahaDashaAnalysisResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[MahaDashaAnalysisData] = None
    
    # Handle direct API response format
    maha_dasha: Optional[str] = None
    analysis: Optional[MahaDashaAnalysisContent] = None

class MahaDashaAnalysisRequest(BaseModel):
    api_key: str = Field(..., description="Your DivineAPI key")
    maha_dasha: str = Field(..., description="Name of Maha Dasha, e.g. 'rahu', 'ketu', 'saturn'")
    lan: Literal["en", "hi"] = "en"

class AntarDashaAnalysisModel(BaseModel):
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None

class AntarDashaAnalysisContent(BaseModel):
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None


class AntarDashaAnalysisData(BaseModel):
    maha_dasha: Optional[str] = None
    antar_dasha: Optional[str] = None
    analysis: Optional[AntarDashaAnalysisContent] = None

class AntarDashaAnalysisResponse(BaseModel):
    success: Optional[int] = None
    data: Optional[AntarDashaAnalysisData] = None
    
    # Handle direct API response format
    maha_dasha: Optional[str] = None
    antar_dasha: Optional[str] = None
    analysis: Optional[AntarDashaAnalysisContent] = None

class AntarDashaAnalysisRequest(BaseModel):
    api_key: str = Field(..., description="Your DivineAPI key")
    maha_dasha: str = Field(..., description="Name of Maha Dasha, e.g. 'rahu'")
    antar_dasha: str = Field(..., description="Name of Antar Dasha, e.g. 'moon'")
    lan: Literal["en", "hi"] = "en"