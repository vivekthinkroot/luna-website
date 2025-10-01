from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date
from kundli.divineapi.intermediate_models import (
    BasicAstroDetailsResponse,
    HoroscopeChartResponse,
    VimshottariDashaResponse,
    MahaDashaAnalysisResponse,
    AntarDashaAnalysisResponse,
    AscendantReportResponse,
    YogasResponse,
    Yoga,
    AshtakavargaResponse,
    GhataChakraResponse,
    GemstoneResponse,
)


class UserProfile1(BaseModel):
    """
    User Profile Page 1: Basic personal and birth information
    Contains: name, gender, date of birth, timezone, place of birth from basic astro details
    """
    name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    timezone: Optional[str] = None
    place_of_birth: Optional[str] = None

    @classmethod
    def from_basic_astro_details(cls, basic_astro: Optional[BasicAstroDetailsResponse]) -> "UserProfile1":
        """Create UserProfile1 from BasicAstroDetailsResponse"""
        if not basic_astro:
            return cls()
        
        # Construct date of birth from year, month, day
        birth_date = None
        if basic_astro.year and basic_astro.month and basic_astro.day:
            try:
                birth_date = date(
                    year=int(basic_astro.year),
                    month=int(basic_astro.month),
                    day=int(basic_astro.day)
                )
            except (ValueError, TypeError):
                birth_date = None
        
        return cls(
            name=basic_astro.full_name,
            gender=basic_astro.gender,
            date_of_birth=birth_date,
            timezone=basic_astro.timezone,
            place_of_birth=basic_astro.place
        )


class UserProfile2(BaseModel):
    """
    User Profile Page 2: Advanced astrological birth information
    Contains: longitude, latitude, Ayanamsa, nakshatra (birth star), moon sign (birth rasi),
    ascendant (Lagna), ascendant lord (Lagna Lord)
    """
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    ayanamsa: Optional[str] = None
    birth_star: Optional[str] = None  # nakshatra from basic astro details
    birth_rasi: Optional[str] = None  # moon sign from basic astro details
    lagna: Optional[str] = None  # ascendant from ascendant report
    lagna_lord: Optional[str] = None  # ascendant lord from ascendant report

    @classmethod
    def from_astro_data(
        cls, 
        basic_astro: Optional[BasicAstroDetailsResponse] = None,
        ascendant_report: Optional[AscendantReportResponse] = None
    ) -> "UserProfile2":
        """Create UserProfile2 from BasicAstroDetailsResponse and AscendantReportResponse"""
        profile = cls()
        
        # Extract from basic astro details
        if basic_astro:
            profile.longitude = basic_astro.longitude
            profile.latitude = basic_astro.latitude
            profile.ayanamsa = basic_astro.ayanamsha
            profile.birth_star = basic_astro.nakshatra
            profile.birth_rasi = basic_astro.moonsign
        
        # Extract from ascendant report
        if ascendant_report:
            profile.lagna = ascendant_report.ascendant
            profile.lagna_lord = ascendant_report.planetary_lord
        
        return profile


class D1Chart(BaseModel):
    """
    D1 Birth Chart (Lagna Chart) - Page 5
    Contains: Birth chart data with SVG or base64 image
    """
    title_main: str = "LAGNA CHART"
    title_sub: str = "BIRTH CHART (D1)"
    chart_description: str = "<strong>D1 Birth Chart:</strong> Shows planetary positions at birth, life path, and personality traits."
    chart_image: Optional[HoroscopeChartResponse] = None
    no_chart_title: str = "D1 Chart Not Available"

    @classmethod
    def from_chart_data(cls, chart_data: Optional[HoroscopeChartResponse]) -> "D1Chart":
        """Create D1Chart from HoroscopeChartResponse"""
        return cls(chart_image=chart_data)


class D9Chart(BaseModel):
    """
    D9 Navamsa Chart - Page 6
    Contains: Navamsa chart data with SVG or base64 image
    """
    title_main: str = "NAVAMSA CHART"
    title_sub: str = "DIVISIONAL CHART (D9)"
    chart_description: str = "<strong>D9 Navamsa Chart:</strong> Reveals marriage compatibility, spiritual growth, and life's second half."
    chart_image: Optional[HoroscopeChartResponse] = None
    no_chart_title: str = "D9 Chart Not Available"

    @classmethod
    def from_chart_data(cls, chart_data: Optional[HoroscopeChartResponse]) -> "D9Chart":
        """Create D9Chart from HoroscopeChartResponse"""
        return cls(chart_image=chart_data)


class AstroInsights(BaseModel):
    """
    Astrological Insights - Page 7 (Remedies)
    Contains: Ghata Chakra, Ascendant details, Lucky stone, Life stone information
    """
    # Main heading and description
    main_heading: str = "Astrological Insights"
    description: str = "Includes relevant astrological facts."
    
    # Grid 1: Ghata Chakra (complete output)
    grid_1_heading: str = "Ghata Chakra"
    grid_1_content: Optional[str] = None
    
    # Grid 2: Ascendant Report details
    grid_2_heading: str = "Ascendant Details"
    grid_2_content: Optional[str] = None
    
    # Grid 3: Lucky Stone details
    grid_3_heading: str = "Lucky Stone"
    grid_3_content: Optional[str] = None
    
    # Grid 4: Life Stone details  
    grid_4_heading: str = "Life Stone"
    grid_4_content: Optional[str] = None

    @classmethod
    def from_astro_data(
        cls,
        ghata_chakra: Optional[GhataChakraResponse] = None,
        ascendant_report: Optional[AscendantReportResponse] = None,
        gemstone: Optional[GemstoneResponse] = None
    ) -> "AstroInsights":
        """Create AstroInsights from various API response data"""
        
        # Grid 1: Format Ghata Chakra data
        ghata_content = "Not Available"
        if ghata_chakra:
            ghata_parts = []
            if ghata_chakra.moon_sign:
                ghata_parts.append(f"Moon Sign: {ghata_chakra.moon_sign}")
            if ghata_chakra.month:
                ghata_parts.append(f"Month: {ghata_chakra.month}")
            if ghata_chakra.tithi:
                ghata_parts.append(f"Tithi: {ghata_chakra.tithi}")
            if ghata_chakra.vaar:
                ghata_parts.append(f"Vaar: {ghata_chakra.vaar}")
            if ghata_chakra.nakshatra:
                ghata_parts.append(f"Nakshatra: {ghata_chakra.nakshatra}")
            if ghata_chakra.yoga:
                ghata_parts.append(f"Yoga: {ghata_chakra.yoga}")
            if ghata_chakra.karana:
                ghata_parts.append(f"Karana: {ghata_chakra.karana}")
            
            if ghata_parts:
                ghata_content = " | ".join(ghata_parts)
        
        # Grid 2: Format Ascendant Report data
        ascendant_content = "Not Available"
        if ascendant_report:
            asc_parts = []
            if ascendant_report.ascendant:
                asc_parts.append(f"Ascendant: {ascendant_report.ascendant}")
            if ascendant_report.planetary_lord:
                asc_parts.append(f"Planetary Lord: {ascendant_report.planetary_lord}")
            if ascendant_report.day_of_fast:
                asc_parts.append(f"Day of Fast: {ascendant_report.day_of_fast}")
            if ascendant_report.characteristics:
                asc_parts.append(f"Characteristics: {ascendant_report.characteristics}")
            
            if asc_parts:
                ascendant_content = " | ".join(asc_parts)
        
        # Grid 3: Format Lucky Stone data
        lucky_stone_content = "Not Available"
        if gemstone and hasattr(gemstone, 'data') and gemstone.data:
            if hasattr(gemstone.data, 'lucky_stone') and gemstone.data.lucky_stone:
                lucky_stone = gemstone.data.lucky_stone
                lucky_parts = []
                
                if hasattr(lucky_stone, 'gemstones') and lucky_stone.gemstones:
                    if hasattr(lucky_stone.gemstones, 'Primary') and lucky_stone.gemstones.Primary:
                        lucky_parts.append(f"Primary Gemstone: {lucky_stone.gemstones.Primary}")
                if hasattr(lucky_stone, 'day_to_wear') and lucky_stone.day_to_wear:
                    lucky_parts.append(f"Day to Wear: {lucky_stone.day_to_wear}")
                if hasattr(lucky_stone, 'finger_to_wear') and lucky_stone.finger_to_wear:
                    lucky_parts.append(f"Finger to Wear: {lucky_stone.finger_to_wear}")
                if hasattr(lucky_stone, 'mantra') and lucky_stone.mantra:
                    lucky_parts.append(f"Mantra: {lucky_stone.mantra}")
                
                if lucky_parts:
                    lucky_stone_content = " | ".join(lucky_parts)
        
        # Grid 4: Format Life Stone data
        life_stone_content = "Not Available"
        if gemstone and hasattr(gemstone, 'data') and gemstone.data:
            if hasattr(gemstone.data, 'life_stone') and gemstone.data.life_stone:
                life_stone = gemstone.data.life_stone
                life_parts = []
                
                if hasattr(life_stone, 'gemstones') and life_stone.gemstones:
                    if hasattr(life_stone.gemstones, 'Primary') and life_stone.gemstones.Primary:
                        life_parts.append(f"Primary Gemstone: {life_stone.gemstones.Primary}")
                if hasattr(life_stone, 'day_to_wear') and life_stone.day_to_wear:
                    life_parts.append(f"Day to Wear: {life_stone.day_to_wear}")
                if hasattr(life_stone, 'finger_to_wear') and life_stone.finger_to_wear:
                    life_parts.append(f"Finger to Wear: {life_stone.finger_to_wear}")
                if hasattr(life_stone, 'mantra') and life_stone.mantra:
                    life_parts.append(f"Mantra: {life_stone.mantra}")
                
                if life_parts:
                    life_stone_content = " | ".join(life_parts)
        
        return cls(
            grid_1_content=ghata_content,
            grid_2_content=ascendant_content,
            grid_3_content=lucky_stone_content,
            grid_4_content=life_stone_content
        )


class AntarDasha(BaseModel):
    """
    Antar Dasha - Page 8
    Contains: Current Maha Dasha and its Antar Dasha periods
    """
    main_title: str = "Antar Dasha"
    maha_dasha_name: Optional[str] = None
    antar_dasha_periods: Optional[List[Dict[str, str]]] = None  # List of {antar_dasha: str, period: str}

    @classmethod
    def from_vimshottari_dasha(cls, vimshottari_dasha: Optional[VimshottariDashaResponse]) -> "AntarDasha":
        """
        Create AntarDasha from VimshottariDashaResponse.
        Uses the current date (datetime.now()) to determine ongoing Maha Dasha and its Antar Dashas.
        """
        from datetime import datetime
        
        maha_dasha_name = "Not Available"
        antar_periods = []
        
        if vimshottari_dasha and vimshottari_dasha.maha_dasha:
            # Find the current running Maha Dasha using ACTUAL current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_maha_dasha = None
            
            for dasha_name, dasha_data in vimshottari_dasha.maha_dasha.items():
                if dasha_data.start_date and dasha_data.end_date:
                    # Check if current date falls within this Maha Dasha period
                    if current_date >= dasha_data.start_date and current_date <= dasha_data.end_date:
                        current_maha_dasha = dasha_name
                        maha_dasha_name = dasha_name
                        break
            
            # If we found the current Maha Dasha, extract its Antar Dasha periods
            if current_maha_dasha and vimshottari_dasha.maha_dasha[current_maha_dasha].antar_dasha:
                for antar_name, antar_data in vimshottari_dasha.maha_dasha[current_maha_dasha].antar_dasha.items():
                    if antar_data.start_time and antar_data.end_time:
                        period_str = f"{antar_data.start_time} to {antar_data.end_time}"
                        antar_periods.append({
                            "antar_dasha": antar_name,
                            "period": period_str
                        })
        
        return cls(
            maha_dasha_name=maha_dasha_name,
            antar_dasha_periods=antar_periods
        )


class DashaAnalysis(BaseModel):
    """
    Dasha Analysis - Page 9-12 (4 pages for Career, Health, Finance, Relationships)
    Contains: Current Maha Dasha, Antar Dasha, and their analysis
    """
    title: str = "Dasha Analysis"
    maha_dasha: Optional[str] = None
    antar_dasha: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    
    # Analysis sections
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    relationships: Optional[str] = None

    @classmethod
    def from_vimshottari_and_analysis(
        cls,
        vimshottari_dasha: Optional[VimshottariDashaResponse] = None,
        antar_dasha_analysis: Optional[AntarDashaAnalysisResponse] = None,
        maha_dasha_analysis: Optional[MahaDashaAnalysisResponse] = None
    ) -> "DashaAnalysis":
        """
        Create DashaAnalysis from VimshottariDashaResponse and AntarDashaAnalysisResponse.
        Uses the current date (datetime.now()) to determine ongoing Maha Dasha.
        """
        from datetime import datetime
        
        maha_dasha = "Not Available"
        antar_dasha = "Not Available"
        start_date = "Not Available"
        end_date = "Not Available"
        description = "Not Available"
        
        # Extract current Maha Dasha and Antar Dasha from Vimshottari using CURRENT DATE
        if vimshottari_dasha and vimshottari_dasha.maha_dasha:
            current_date = datetime.now().strftime("%Y-%m-%d")  # Use ACTUAL current date, not birth date
            current_maha_dasha = None
            current_antar_dasha = None
            
            for dasha_name, dasha_data in vimshottari_dasha.maha_dasha.items():
                if dasha_data.start_date and dasha_data.end_date:
                    if current_date >= dasha_data.start_date and current_date <= dasha_data.end_date:
                        current_maha_dasha = dasha_name
                        maha_dasha = dasha_name
                        
                        # Find current Antar Dasha
                        if dasha_data.antar_dasha:
                            for antar_name, antar_data in dasha_data.antar_dasha.items():
                                if antar_data.start_time and antar_data.end_time:
                                    if current_date >= antar_data.start_time and current_date <= antar_data.end_time:
                                        current_antar_dasha = antar_name
                                        antar_dasha = antar_name
                                        start_date = antar_data.start_time
                                        end_date = antar_data.end_time
                                        break
                        break
        
        # Extract analysis data (prioritize Maha Dasha analysis over Antar Dasha)
        career = "Not Available"
        health = "Not Available"
        finance = "Not Available"
        relationships = "Not Available"
        
        # First try to get from Maha Dasha analysis (most detailed)
        if maha_dasha_analysis:
            if maha_dasha_analysis.data and maha_dasha_analysis.data.analysis:
                analysis = maha_dasha_analysis.data.analysis
                career = analysis.career or "Not Available"
                health = analysis.health or "Not Available"
                finance = analysis.finance or "Not Available"
                relationships = analysis.relationships or "Not Available"
            elif maha_dasha_analysis.analysis:
                analysis = maha_dasha_analysis.analysis
                career = analysis.career or "Not Available"
                health = analysis.health or "Not Available"
                finance = analysis.finance or "Not Available"
                relationships = analysis.relationships or "Not Available"
        
        # Fallback to Antar Dasha analysis if Maha Dasha analysis not available
        if career == "Not Available" and antar_dasha_analysis:
            if antar_dasha_analysis.data and antar_dasha_analysis.data.analysis:
                analysis = antar_dasha_analysis.data.analysis
                career = analysis.career or "Not Available"
                health = analysis.health or "Not Available"
                finance = analysis.finance or "Not Available"
                relationships = analysis.relationships or "Not Available"
            elif antar_dasha_analysis.analysis:
                analysis = antar_dasha_analysis.analysis
                career = analysis.career or "Not Available"
                health = analysis.health or "Not Available"
                finance = analysis.finance or "Not Available"
                relationships = analysis.relationships or "Not Available"
        
        # Create description
        if maha_dasha != "Not Available" and antar_dasha != "Not Available":
            description = f"Analysis of {antar_dasha} Antar Dasha within {maha_dasha} Maha Dasha"
        
        return cls(
            maha_dasha=maha_dasha,
            antar_dasha=antar_dasha,
            start_date=start_date,
            end_date=end_date,
            description=description,
            career=career,
            health=health,
            finance=finance,
            relationships=relationships
        )


class Yogas(BaseModel):
    """
    Yogas - Pages 13+ (Multiple pages for each valid yoga)
    Contains: List of valid yogas with their names and descriptions
    """
    title: str = "Yogas - Special Combination of Planets"
    description: str = "Yogas are special combination of planets in the horoscope which influence the life and future of a person. Some are formed by simple conjunction of planets,whereas others are based on complex astrological logic or peculiar placement of planets in the chart."
    valid_yogas: List[Dict[str, str]] = []  # List of {name: str, description: str}

    @classmethod
    def from_yogas_response(cls, yogas_response: Optional[YogasResponse]) -> "Yogas":
        """
        Create Yogas from YogasResponse
        Extracts all yogas where is_valid is "true"
        """
        valid_yogas = []
        
        if yogas_response and yogas_response.data:
            data = yogas_response.data
            
            # Helper function to process individual yoga
            def process_yoga(yoga: Optional[Yoga]) -> Optional[Dict[str, str]]:
                if yoga and yoga.is_valid == "true" and yoga.name and yoga.content and yoga.content.detail:
                    description = " ".join(yoga.content.detail)
                    return {"name": yoga.name, "description": description}
                return None
            
            # Process all individual yogas
            yoga_fields = [
                data.raj_yoga, data.vipreet_raj_yoga, data.dhan_yoga, data.buddha_aditya_yoga,
                data.gaja_kesari_yoga, data.amala_yoga, data.parvata_yoga, data.kahala_yoga,
                data.chamara_yoga, data.sankha_yoga, data.lagnadhi_yoga, data.chandradhi_yoga,
                data.shubh_kartari_yoga, data.paap_kartari_yoga, data.saraswati_yoga,
                data.lakshmi_yoga, data.kusuma_yoga, data.kalindi_yoga, data.kalpadruma_yoga,
                data.khadga_yoga, data.koorma_yoga, data.matsya_yoga, data.sarada_yoga,
                data.srinatha_yoga, data.mridanga_yoga, data.bheri_yoga
            ]
            
            for yoga in yoga_fields:
                result = process_yoga(yoga)
                if result:
                    valid_yogas.append(result)
            
            # Process Pancha Mahapurusha Yogas
            if data.pancha_mahapurusha_yoga:
                pancha_yogas = [
                    data.pancha_mahapurusha_yoga.bhadra_pancha_mahapurusha_yoga,
                    data.pancha_mahapurusha_yoga.malavya_pancha_mahapurusha_yoga,
                    data.pancha_mahapurusha_yoga.ruchaka_pancha_mahapurusha_yoga,
                    data.pancha_mahapurusha_yoga.hamsa_pancha_mahapurusha_yoga,
                    data.pancha_mahapurusha_yoga.sasha_pancha_mahapurusha_yoga
                ]
                for yoga in pancha_yogas:
                    result = process_yoga(yoga)
                    if result:
                        valid_yogas.append(result)
            
            # Process Lunar Yogas
            if data.lunar_yoga:
                lunar_yogas = [
                    data.lunar_yoga.sunapha_yoga,
                    data.lunar_yoga.anapha_yoga,
                    data.lunar_yoga.duradhara_yoga
                ]
                for yoga in lunar_yogas:
                    result = process_yoga(yoga)
                    if result:
                        valid_yogas.append(result)
            
            # Process Solar Yogas
            if data.solar_yoga:
                solar_yogas = [
                    data.solar_yoga.vesi_yoga,
                    data.solar_yoga.vasi_yoga,
                    data.solar_yoga.ubhayachari_yoga
                ]
                for yoga in solar_yogas:
                    result = process_yoga(yoga)
                    if result:
                        valid_yogas.append(result)
            
            # Process Trimurti Yogas
            if data.trimurti_yogas:
                trimurti_yogas = [
                    data.trimurti_yogas.hari_yoga,
                    data.trimurti_yogas.hara_yoga,
                    data.trimurti_yogas.brahma_yoga
                ]
                for yoga in trimurti_yogas:
                    result = process_yoga(yoga)
                    if result:
                        valid_yogas.append(result)
        
        return cls(valid_yogas=valid_yogas)


class AstroChartOutput(BaseModel):
    chart_id: str
    chart_data: HoroscopeChartResponse


class FinalAstroOutput(BaseModel):
    """
    Clean final output containing only the processed user profile models and chart models.
    This model provides a simplified, structured interface for accessing user data.
    """
    user_profile1: Optional[UserProfile1] = None
    user_profile2: Optional[UserProfile2] = None
    d1_chart: Optional[D1Chart] = None
    d9_chart: Optional[D9Chart] = None
    astro_insights: Optional[AstroInsights] = None
    antar_dasha: Optional[AntarDasha] = None
    dasha_analysis: Optional[DashaAnalysis] = None
    yogas: Optional[Yogas] = None, # NEW
    ashtakavarga: Optional[AshtakavargaResponse] = None

    @classmethod
    def from_raw_data(
        cls,
        basic_astro_details: Optional[BasicAstroDetailsResponse] = None,
        ascendant_report: Optional[AscendantReportResponse] = None,
        vimshottari_dasha: Optional[VimshottariDashaResponse] = None,
        saturn_maha_dasha_analysis: Optional[MahaDashaAnalysisResponse] = None,
        mercury_maha_dasha_analysis: Optional[MahaDashaAnalysisResponse] = None,
        antar_dasha_analysis: Optional[AntarDashaAnalysisResponse] = None,
        charts: List[AstroChartOutput] = None,
        yogas: Optional[YogasResponse] = None,
        ashtakavarga: Optional[AshtakavargaResponse] = None,
        ghata_chakra: Optional[GhataChakraResponse] = None,
        gemstone: Optional[GemstoneResponse] = None
    ) -> "FinalAstroOutput":
        """
        Create FinalAstroOutput from raw API response data.
        This factory method processes the raw data and extracts only the relevant user profile information.
        """
        # Generate clean user profile models from raw data
        user_profile1 = UserProfile1.from_basic_astro_details(basic_astro_details)
        user_profile2 = UserProfile2.from_astro_data(
            basic_astro=basic_astro_details,
            ascendant_report=ascendant_report
        )
        
        # Extract D1 and D9 charts from charts list
        d1_chart_data = None
        d9_chart_data = None
        
        if charts:
            for chart in charts:
                if chart.chart_id == "D1":
                    d1_chart_data = chart.chart_data
                elif chart.chart_id == "D9":
                    d9_chart_data = chart.chart_data
        
        # Create chart models
        d1_chart = D1Chart.from_chart_data(d1_chart_data)
        d9_chart = D9Chart.from_chart_data(d9_chart_data)
        
        # Create astro insights model
        astro_insights = AstroInsights.from_astro_data(
            ghata_chakra=ghata_chakra,
            ascendant_report=ascendant_report,
            gemstone=gemstone
        )
        
        # Create antar dasha model
        antar_dasha = AntarDasha.from_vimshottari_dasha(vimshottari_dasha)
        
        # Create dasha analysis model
        dasha_analysis = DashaAnalysis.from_vimshottari_and_analysis(
            vimshottari_dasha=vimshottari_dasha,
            antar_dasha_analysis=antar_dasha_analysis,
            maha_dasha_analysis=saturn_maha_dasha_analysis  # Now contains current Maha Dasha analysis
        )
        
        # Create yogas model
        yogas_model = Yogas.from_yogas_response(yogas)
        
        return cls(
            user_profile1=user_profile1,
            user_profile2=user_profile2,
            d1_chart=d1_chart,
            d9_chart=d9_chart,
            astro_insights=astro_insights,
            antar_dasha=antar_dasha,
            dasha_analysis=dasha_analysis,
            yogas=yogas_model, # NEW
            ashtakavarga=ashtakavarga
        )
