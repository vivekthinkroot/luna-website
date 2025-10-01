"""
CitiesDAO implementation for Luna.
Handles direct database operations for cities data from pgAdmin database.
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel
from sqlmodel import col, func, select

from data.db import get_session
from data.models import TCities


class CityCandidate(BaseModel):
    id: int
    city: str
    city_ascii: Optional[str] = None
    country: Optional[str] = None
    admin_name: Optional[str] = None  # This is the state/region field
    lat: Optional[float] = None  # Latitude
    lng: Optional[float] = None  # Longitude
    population: Optional[float] = None

    model_config = {"from_attributes": True}


class CitiesDAO:
    """Data access object for cities operations using pgAdmin PostgreSQL database."""

    def get_exact_matches(self, city_name: str) -> List[CityCandidate]:
        """Get exact matches from cities database."""
        normalized_name = city_name.strip().title()

        with get_session() as db:
            # Exact match
            result = db.exec(
                select(TCities).where(TCities.city == normalized_name)
            )
            exact_matches = result.all()

            if not exact_matches:
                # Case-insensitive match
                result = db.exec(
                    select(TCities).where(
                        func.lower(TCities.city) == normalized_name.lower()
                    )
                )
                exact_matches = result.all()

            return [self._convert_to_candidate(city) for city in exact_matches]

    def get_contains_matches(
        self, city_name: str, limit: int = 10
    ) -> List[CityCandidate]:
        """Get cities containing the search term."""
        normalized_name = city_name.strip()

        with get_session() as db:
            result = db.exec(
                select(TCities)
                .where(func.lower(TCities.city).like(f"%{normalized_name.lower()}%"))
                .limit(limit)
            )
            return [self._convert_to_candidate(city) for city in result.all()]

    def get_all_city_names(self) -> List[Tuple[str, int]]:
        """Get all city names and IDs for fuzzy matching."""
        with get_session() as db:
            result = db.exec(select(TCities.city, TCities.id))
            return [
                (name, city_id) for name, city_id in result.all() if city_id is not None
            ]

    def get_cities_by_ids(self, city_ids: List[int]) -> List[CityCandidate]:
        """Get multiple cities by their IDs."""
        with get_session() as db:
            result = db.exec(
                select(TCities).where(col(TCities.id).in_(city_ids))
            )
            return [self._convert_to_candidate(city) for city in result.all()]

    def get_city_by_id(self, city_id: int) -> Optional[CityCandidate]:
        """Get single city by ID."""
        with get_session() as db:
            result = db.exec(select(TCities).where(TCities.id == city_id))
            city = result.one_or_none()
            if city:
                return self._convert_to_candidate(city)
            return None

    def search_cities_optimized(self, search_term: str, limit: int = 20) -> List[CityCandidate]:
        """
        Optimized city search using multiple strategies for best performance.
        
        Args:
            search_term: The search term to look for
            limit: Maximum number of results to return
            
        Returns:
            List of CityCandidate objects sorted by relevance
        """
        normalized_term = search_term.strip().title()
        
        with get_session() as db:
            # Strategy 1: Exact match (highest priority)
            exact_result = db.exec(
                select(TCities).where(TCities.city == normalized_term)
            )
            exact_matches = [self._convert_to_candidate(city) for city in exact_result.all()]
            
            if len(exact_matches) >= limit:
                return exact_matches[:limit]
            
            # Strategy 2: Case-insensitive exact match
            if not exact_matches:
                case_insensitive_result = db.exec(
                    select(TCities).where(
                        func.lower(TCities.city) == normalized_term.lower()
                    )
                )
                exact_matches = [self._convert_to_candidate(city) for city in case_insensitive_result.all()]
            
            if len(exact_matches) >= limit:
                return exact_matches[:limit]
            
            # Strategy 3: Starts with search (high priority)
            starts_with_result = db.exec(
                select(TCities)
                .where(func.lower(TCities.city).like(f"{normalized_term.lower()}%"))
                .limit(limit - len(exact_matches))
            )
            starts_with_matches = [self._convert_to_candidate(city) for city in starts_with_result.all()]
            
            combined_results = exact_matches + starts_with_matches
            if len(combined_results) >= limit:
                return combined_results[:limit]
            
            # Strategy 4: Contains search (medium priority)
            contains_result = db.exec(
                select(TCities)
                .where(func.lower(TCities.city).like(f"%{normalized_term.lower()}%"))
                .limit(limit - len(combined_results))
            )
            contains_matches = [self._convert_to_candidate(city) for city in contains_result.all()]
            
            combined_results.extend(contains_matches)
            return combined_results[:limit]

    def get_cities_by_country(self, country: str, limit: int = 50) -> List[CityCandidate]:
        """Get cities by country."""
        with get_session() as db:
            result = db.exec(
                select(TCities)
                .where(func.lower(TCities.country) == country.lower())
                .limit(limit)
            )
            return [self._convert_to_candidate(city) for city in result.all()]

    def get_popular_cities(self, limit: int = 20) -> List[CityCandidate]:
        """Get most popular cities (by population)."""
        with get_session() as db:
            result = db.exec(
                select(TCities)
                .where(TCities.population.isnot(None))
                .order_by(TCities.population.desc())
                .limit(limit)
            )
            return [self._convert_to_candidate(city) for city in result.all()]

    def _convert_to_candidate(self, city: TCities) -> CityCandidate:
        """Convert database model to CityCandidate."""
        if city.id is None:
            raise ValueError("city.id cannot be None")

        return CityCandidate(
            id=city.id,
            city=city.city,
            city_ascii=city.city_ascii,
            country=city.country,
            admin_name=city.admin_name,
            lat=city.lat,
            lng=city.lng,
            population=city.population,
        )
