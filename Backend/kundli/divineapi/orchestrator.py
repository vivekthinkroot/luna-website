from typing import Dict

from .client import DivineAPIClient
from .output_model import FinalAstroOutput, AstroChartOutput
from .intermediate_models import (
    GemstoneRequest,
    YogasRequest,
    AshtakavargaRequest,
    MahaDashaAnalysisRequest,
    AntarDashaAnalysisRequest,
)


def generate_kundli_orchestrator(user_input: Dict) -> FinalAstroOutput:
    client = DivineAPIClient()

    # Basic astro details
    basic = client.fetch_basic_astro_details(user_input)
    
    # Horoscope charts (D1 and D9)
    chart_d1 = client.fetch_horoscope_chart(user_input, chart_id="D1")
    chart_d9 = client.fetch_horoscope_chart(user_input, chart_id="D9")
    charts = [
        AstroChartOutput(chart_id="D1", chart_data=chart_d1),
        AstroChartOutput(chart_id="D9", chart_data=chart_d9)
    ]

    # Vimshottari dasha
    v_dasha = client.fetch_vimshottari_dasha(user_input)
    
    # Determine current Maha Dasha from Vimshottari Dasha
    from datetime import datetime
    current_maha_dasha_planet = None
    
    if v_dasha and v_dasha.maha_dasha:
        # Use current date to find ongoing Maha Dasha
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"DEBUG: Current date for Maha Dasha detection: {current_date_str}")
        
        for dasha_name, dasha_data in v_dasha.maha_dasha.items():
            if dasha_data.start_date and dasha_data.end_date:
                # Check if current date falls within this Maha Dasha period
                if current_date_str >= dasha_data.start_date and current_date_str <= dasha_data.end_date:
                    current_maha_dasha_planet = dasha_name
                    print(f"DEBUG: Current Maha Dasha detected: {current_maha_dasha_planet}")
                    print(f"  Period: {dasha_data.start_date} to {dasha_data.end_date}")
                    break
    
    if not current_maha_dasha_planet:
        # Fallback to first Maha Dasha if current not found
        if v_dasha and v_dasha.maha_dasha:
            current_maha_dasha_planet = list(v_dasha.maha_dasha.keys())[0]
            print(f"DEBUG: No current Maha Dasha found, using first: {current_maha_dasha_planet}")
        else:
            current_maha_dasha_planet = "Sun"  # Final fallback
            print(f"DEBUG: Using default Maha Dasha: {current_maha_dasha_planet}")
    
    # Maha-dasha analysis for current ongoing Maha Dasha - with error handling
    current_maha_dasha_analysis = None
    try:
        maha_dasha_request = MahaDashaAnalysisRequest(
            api_key=user_input.get("api_key", ""),
            maha_dasha=current_maha_dasha_planet,
            lan="en"
        )
        current_maha_dasha_analysis = client.fetch_maha_dasha_analysis(maha_dasha_request)
        print(f"DEBUG: Successfully fetched analysis for {current_maha_dasha_planet} Maha Dasha")
    except Exception as e:
        print(f"Warning: {current_maha_dasha_planet} Maha Dasha analysis failed: {e}")
        current_maha_dasha_analysis = None
    
    # Antar dasha analysis - requires specific request object with error handling
    try:
        # Use the detected current Maha Dasha
        current_antar_dasha = current_maha_dasha_planet  # Default to same planet
        
        # Find current Antar Dasha within the current Maha Dasha
        if v_dasha and v_dasha.maha_dasha and current_maha_dasha_planet:
            maha_data = v_dasha.maha_dasha.get(current_maha_dasha_planet)
            if maha_data and maha_data.antar_dasha:
                for antar_name, antar_data in maha_data.antar_dasha.items():
                    if antar_data.start_time and antar_data.end_time:
                        if current_date_str >= antar_data.start_time and current_date_str <= antar_data.end_time:
                            current_antar_dasha = antar_name
                            print(f"DEBUG: Current Antar Dasha detected: {current_antar_dasha}")
                            print(f"  Period: {antar_data.start_time} to {antar_data.end_time}")
                            break
        
        print(f"DEBUG: Fetching Antar Dasha analysis for {current_maha_dasha_planet}/{current_antar_dasha}")
        
        antar_dasha_request = AntarDashaAnalysisRequest(
            api_key=user_input.get("api_key", ""),
            maha_dasha=current_maha_dasha_planet,
            antar_dasha=current_antar_dasha,
            lan="en"
        )
        antar_dasha = client.fetch_antar_dasha_analysis(antar_dasha_request)
        print(f"DEBUG: Successfully fetched Antar Dasha analysis")
    except Exception as e:
        print(f"Warning: Antar Dasha analysis failed: {e}")
        antar_dasha = None
    
    # Ascendant report
    asc = client.fetch_ascendant_report(user_input)
    
    # Yogas - requires specific request object with error handling
    try:
        yogas_request = YogasRequest(**user_input)
        yogas = client.fetch_yogas(yogas_request)
    except Exception as e:
        print(f"Warning: Yogas analysis failed: {e}")
        yogas = None
    
    # Ashtakavarga - requires specific request object with error handling
    try:
        ashtakavarga_request = AshtakavargaRequest(**user_input)
        ashtakavarga = client.fetch_ashtakavarga(ashtakavarga_request)
    except Exception as e:
        print(f"Warning: Ashtakavarga analysis failed: {e}")
        ashtakavarga = None
    
    # Ghata chakra with error handling
    try:
        ghata = client.fetch_ghata_chakra(user_input)
    except Exception as e:
        print(f"Warning: Ghata Chakra analysis failed: {e}")
        ghata = None
    
    # Gemstone - requires specific request object with error handling
    try:
        print(f"DEBUG: Creating GemstoneRequest with user_input keys: {user_input.keys()}")
        
        # Map 'min' to 'minute', 'lon' to 'lon', 'sec' to 'second' for GemstoneRequest
        gemstone_input = user_input.copy()
        if 'min' in gemstone_input and 'minute' not in gemstone_input:
            gemstone_input['minute'] = gemstone_input['min']
        if 'sec' in gemstone_input and 'second' not in gemstone_input:
            gemstone_input['second'] = gemstone_input['sec']
        
        # Ensure required field 'lan' is present (language)
        if 'lan' not in gemstone_input:
            gemstone_input['lan'] = 'en'
        
        print(f"DEBUG: Creating GemstoneRequest with mapped fields: {gemstone_input.keys()}")
        gemstone_request = GemstoneRequest(**gemstone_input)
        print(f"DEBUG: GemstoneRequest created successfully: {gemstone_request}")
        gemstone = client.fetch_gemstone(gemstone_request)
        print(f"DEBUG: Gemstone response received: success={getattr(gemstone, 'success', 'N/A')}")
        if gemstone and hasattr(gemstone, 'data') and gemstone.data:
            print(f"DEBUG: Gemstone data found (lucky_stone, life_stone, dasha_stone)")
        else:
            print(f"DEBUG: Gemstone response has no data or is None")
    except Exception as e:
        print(f"Warning: Gemstone analysis failed: {e}")
        import traceback
        traceback.print_exc()
        gemstone = None

    return FinalAstroOutput.from_raw_data(
        basic_astro_details=basic,
        ascendant_report=asc,
        vimshottari_dasha=v_dasha,
        saturn_maha_dasha_analysis=current_maha_dasha_analysis,  # Using current ongoing Maha Dasha
        mercury_maha_dasha_analysis=None,  # No longer used, keeping for backward compatibility
        antar_dasha_analysis=antar_dasha,
        charts=charts,
        yogas=yogas,
        ashtakavarga=ashtakavarga,
        ghata_chakra=ghata,
        gemstone=gemstone,
    )
