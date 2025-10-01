import os
from typing import Dict

import requests
from dotenv import load_dotenv

from kundli.divineapi.intermediate_models import (
    AntarDashaAnalysisRequest,
    AntarDashaAnalysisResponse,
    AntarDashaRequest,
    AntarDashaResponse,
    AscendantReportResponse,
    AshtakavargaRequest,
    AshtakavargaResponse,
    BasicAstroDetailsResponse,
    BhavaKundliRequest,
    BhavaKundliResponse,
    CompositeFriendshipResponse,
    GemstoneRequest,
    GemstoneResponse,
    GhataChakraResponse,
    HoroscopeChartResponse,
    KaalChakraRequest,
    KaalChakraResponse,
    KaalSarpaDoshaResponse,
    KPChartRequest,
    KPChartResponse,
    KPCuspalResponse,
    KPPlanetaryPositionsResponse,
    MahaDashaAnalysisRequest,
    MahaDashaAnalysisResponse,
    ManglikDoshaResponse,
    PlanetAnalysisRequest,
    PlanetAnalysisResponse,
    PlanetaryPositionsResponse,
    PratyantarDashaRequest,
    PratyantarDashaResponse,
    SadheSatiResponse,
    ShadbalaRequest,
    ShadbalaResponse,
    SubPlanetChartResponse,
    SubPlanetPositionsResponse,
    SudarshanaRequest,
    SudarshanaResponse,
    VimshottariDashaResponse,
    YogasRequest,
    YogasResponse,
    YoginiDashaRequest,
    YoginiDashaResponse,
)

load_dotenv()


class DivineAPIClient:
    def __init__(self) -> None:
        self.auth_token = os.getenv("AUTH_TOKEN", "")
        self.api_key = os.getenv("DIVINE_API_KEY", "")
        # Bypass TLS cert verification if env not set to truthy (default: bypass for unstable envs/tests)
        self._verify_tls = self._parse_bool(os.getenv("DIVINE_API_VERIFY_TLS", "0"))

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

    @staticmethod
    def _parse_bool(value: str) -> bool:
        v = value.strip().lower()
        return v in ("1", "true", "yes", "on")

    def _prepare_payload(self, user_data: Dict) -> Dict:
        payload = user_data.copy()
        payload["api_key"] = self.api_key
        return payload

    def _post(self, url: str, payload: Dict) -> Dict:
        # Follow the final microservice pattern: use data=payload instead of json=payload
        response = requests.post(
            url,
            headers=self._headers(),
            data=payload,  # Use data instead of json like final microservice
            verify=False,
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()

        # Only treat as error if API explicitly returns success != 1 (like final microservice)
        if result.get("success") != 1:
            print(f"API Error for {url}: {result.get('msg', 'Unknown error')}")
            # Raise exception to fail fast when credentials are wrong
            raise ValueError(f"API Error: {result.get('msg', 'Unknown error')}")

        # Return the data portion if success = 1 (like final microservice)
        return result.get("data", result)

    def fetch_basic_astro_details(self, user_data: Dict) -> BasicAstroDetailsResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v3/basic-astro-details"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return BasicAstroDetailsResponse(**data)

    def fetch_planetary_positions(self, user_data: Dict) -> PlanetaryPositionsResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/planetary-positions"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return PlanetaryPositionsResponse(**data)

    def fetch_composite_friendship(
        self, user_data: Dict
    ) -> CompositeFriendshipResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/composite-friendship"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return CompositeFriendshipResponse(**data)

    def fetch_horoscope_chart(
        self, user_data: Dict, chart_id: str = "D1"
    ) -> HoroscopeChartResponse:
        url = (
            f"https://astroapi-3.divineapi.com/indian-api/v1/horoscope-chart/{chart_id}"
        )
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return HoroscopeChartResponse(**data)

    def fetch_vimshottari_dasha(self, user_data: Dict) -> VimshottariDashaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha"
        payload = self._prepare_payload(user_data)
        payload["dasha_type"] = "antar-dasha"
        data = self._post(url, payload)
        return VimshottariDashaResponse(**data)

    def fetch_sadhe_sati(self, user_data: Dict) -> SadheSatiResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/sadhe-sati"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return SadheSatiResponse(**data)

    def fetch_kaal_sarpa_dosha(self, user_data: Dict) -> KaalSarpaDoshaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/kaal-sarpa-yoga"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return KaalSarpaDoshaResponse(**data)

    def fetch_manglik_dosha(self, user_data: Dict) -> ManglikDoshaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/manglik-dosha"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return ManglikDoshaResponse(**data)

    def fetch_ascendant_report(self, user_data: Dict) -> AscendantReportResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/ascendant-report"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return AscendantReportResponse(**data)

    def fetch_ghata_chakra(self, user_data: Dict) -> GhataChakraResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/ghata-chakra"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return GhataChakraResponse(**data)

    # Additional endpoints (moved into the class and made synchronous)
    def fetch_sub_planet_positions(self, user_data: Dict) -> SubPlanetPositionsResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/sub-planet-positions"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return SubPlanetPositionsResponse(**data)

    def fetch_sub_planet_chart(self, user_data: Dict) -> SubPlanetChartResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/sub-planet-chart"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return SubPlanetChartResponse(**data)

    def fetch_kp_planetary_positions(
        self, user_data: Dict
    ) -> KPPlanetaryPositionsResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/kp/planetary-positions"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return KPPlanetaryPositionsResponse(**data)

    def fetch_kp_cuspal(self, user_data: Dict) -> KPCuspalResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/kp/cuspal"
        payload = self._prepare_payload(user_data)
        data = self._post(url, payload)
        return KPCuspalResponse(**data)

    def fetch_kp_chart(self, type_id: str, payload: KPChartRequest) -> KPChartResponse:
        url = f"https://astroapi-3.divineapi.com/indian-api/v1/kp/{type_id}"
        data = self._post(url, payload.dict())
        return KPChartResponse(**data)

    def fetch_bhava_kundli(self, payload: BhavaKundliRequest) -> BhavaKundliResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/bhava-kundli"
        data = self._post(url, payload.dict())
        return BhavaKundliResponse(**data)

    def fetch_pratyantar_dasha(self, payload: PratyantarDashaRequest) -> PratyantarDashaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/pratyantar-dasha"
        data = self._post(url, payload.dict())
        return PratyantarDashaResponse(**data)

    def fetch_shadbala(self, payload: ShadbalaRequest) -> ShadbalaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/shadbala"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        return ShadbalaResponse(**response.json())

    def fetch_gemstone(self, payload: GemstoneRequest) -> GemstoneResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/gemstone-suggestion"
        # Convert payload to form data format as required by the API
        form_data = {
            'api_key': self.api_key,
            'full_name': payload.full_name,
            'day': str(payload.day),
            'month': str(payload.month),
            'year': str(payload.year),
            'hour': str(payload.hour),
            'min': str(payload.minute),
            'sec': str(payload.second),
            'gender': payload.gender,
            'place': payload.place,
            'lat': str(payload.lat),
            'lon': str(payload.lon),
            'tzone': str(payload.tzone),
            'lan': payload.lan
        }
        response = requests.post(
            url,
            data=form_data,
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        
        # Handle empty lists in response data (API sometimes returns [] instead of null)
        response_data = response.json()
        if response_data.get('data'):
            data = response_data['data']
            # Convert empty lists to None
            if data.get('dasha_stone') == []:
                data['dasha_stone'] = None
            if data.get('lucky_stone') == []:
                data['lucky_stone'] = None
            if data.get('life_stone') == []:
                data['life_stone'] = None
        
        return GemstoneResponse(**response_data)

    def fetch_yogini_dasha(self, payload: YoginiDashaRequest) -> YoginiDashaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/yogini_dasha"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        return YoginiDashaResponse(**response.json())

    def fetch_yogas(self, payload: YogasRequest) -> YogasResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/yogas"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        return YogasResponse(**response.json())

    def fetch_kaal_chakra(self, payload: KaalChakraRequest) -> KaalChakraResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/kaal_chakra_dasha"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        return KaalChakraResponse(**response.json())

    def fetch_sudarshana(self, payload: SudarshanaRequest) -> SudarshanaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/sudarshana_chakra"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        return SudarshanaResponse(**response.json())

    def fetch_planet_analysis(
        self, payload: PlanetAnalysisRequest
    ) -> PlanetAnalysisResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v2/planet_analysis"
        response = requests.post(
            url,
            json=payload.dict(),
            headers=self._headers(),
            timeout=60,
            verify=self._verify_tls,
        )
        response.raise_for_status()
        return PlanetAnalysisResponse(**response.json())

    def fetch_ashtakavarga(self, payload: AshtakavargaRequest) -> AshtakavargaResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/bhinnashtakvarga/ashtakvarga"
        # Convert payload to dict and add API key
        payload_dict = payload.dict()
        payload_dict["api_key"] = self.api_key
        
        response = requests.post(
            url,
            data=payload_dict,
            headers=self._headers(),
            timeout=60,
            verify=False,
        )
        response.raise_for_status()
        result = response.json()
        
        # Check if API returned an error
        if result.get("success") != 1:
            raise ValueError(f"Ashtakavarga API Error: {result.get('msg', 'Unknown error')}")
        
        # Transform the API response to match AshtakavargaResponse structure
        data = result.get("data", {})
        table = data.get("table", {})
        
        # Convert table data to PlanetAshtakavarga list
        planet_data_list = []
        total_points_dict = {}
        
        for planet, planet_data in table.items():
            if isinstance(planet_data, dict) and 'total' in planet_data:
                total_data = planet_data['total']
                if isinstance(total_data, dict) and 'points' in total_data:
                    total_points = total_data['points']
                    total_points_dict[planet] = total_points
                    
                    # Extract house-wise points
                    house_wise_points = {}
                    for key, value in total_data.items():
                        if key.isdigit():  # House numbers
                            house_wise_points[f"House{key}"] = value
                    
                    planet_data_list.append({
                        "planet": planet,
                        "house_wise_points": house_wise_points,
                        "total_points": total_points
                    })
        
        # Create the transformed response
        transformed_result = {
            "success": result.get("success", 1),
            "data": planet_data_list,
            "total_points": total_points_dict
        }
        
        return AshtakavargaResponse(**transformed_result)

    def fetch_maha_dasha_analysis(self, payload: MahaDashaAnalysisRequest) -> MahaDashaAnalysisResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/maha-dasha-analysis"
        response = requests.post(
        url,
        json=payload.dict(),
        headers=self._headers(),
        timeout=60,
        verify=self._verify_tls,
    )
        response.raise_for_status()
        return MahaDashaAnalysisResponse(**response.json().get("data", {}))

    def fetch_antar_dasha_analysis(self, payload: AntarDashaAnalysisRequest) -> AntarDashaAnalysisResponse:
        url = "https://astroapi-3.divineapi.com/indian-api/v1/antar-dasha-analysis"
        response = requests.post(
        url,
        json=payload.dict(),
        headers=self._headers(),
        timeout=60,
        verify=self._verify_tls,
    )
        response.raise_for_status()
        return AntarDashaAnalysisResponse(**response.json().get("data", {}))
