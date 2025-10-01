"""
GeolocationDAO implementation for Luna.
Handles direct database operations for geolocation data.
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel
from sqlmodel import col, func, select

from data.db import get_session
from data.models import TLocations


class LocationCandidate(BaseModel):
    id: int
    source_id: Optional[int] = None
    city: str
    country: Optional[str] = None
    province: Optional[str] = None
    latitude: float
    longitude: float
    timezone: Optional[str] = None
    population: Optional[int] = None

    model_config = {"from_attributes": True}


# dao object for geolocation
class GeolocationDAO:
    """Data access object for geolocation operations using local PostgreSQL."""

    def get_exact_matches(self, location_name: str) -> List[LocationCandidate]:
        """Get exact matches from database."""
        normalized_name = location_name.strip().title()

        with get_session() as db:
            # Exact match
            result = db.exec(
                select(TLocations).where(TLocations.city == normalized_name)
            )
            exact_matches = result.all()

            if not exact_matches:
                # Case-insensitive match
                result = db.exec(
                    select(TLocations).where(
                        func.lower(TLocations.city) == normalized_name.lower()
                    )
                )
                exact_matches = result.all()

            return [self._convert_to_candidate(loc) for loc in exact_matches]

    def get_contains_matches(
        self, location_name: str, limit: int = 10
    ) -> List[LocationCandidate]:
        """Get locations containing the search term."""
        normalized_name = location_name.strip()

        with get_session() as db:
            result = db.exec(
                select(TLocations)
                .where(func.lower(TLocations.city).like(f"%{normalized_name.lower()}%"))
                .limit(limit)
            )
            return [self._convert_to_candidate(loc) for loc in result.all()]

    def get_all_city_names(self) -> List[Tuple[str, int]]:
        """Get all city names and IDs for fuzzy matching."""
        with get_session() as db:
            result = db.exec(select(TLocations.city, TLocations.id))
            return [
                (city, loc_id) for city, loc_id in result.all() if loc_id is not None
            ]

    def get_locations_by_ids(self, location_ids: List[int]) -> List[LocationCandidate]:
        """Get multiple locations by their IDs."""
        with get_session() as db:
            result = db.exec(
                select(TLocations).where(col(TLocations.id).in_(location_ids))
            )
            return [self._convert_to_candidate(loc) for loc in result.all()]

    def get_location_by_id(self, location_id: int) -> Optional[LocationCandidate]:
        """Get single location by ID."""
        with get_session() as db:
            result = db.exec(select(TLocations).where(TLocations.id == location_id))
            location = result.one_or_none()
            if location:
                return self._convert_to_candidate(location)
            return None

    def _convert_to_candidate(self, location: TLocations) -> LocationCandidate:
        """Convert database model to LocationCandidate."""
        if location.id is None:
            raise ValueError("location.id cannot be None")

        return LocationCandidate(
            id=location.id,
            source_id=location.source_id,
            city=location.city,
            country=location.country,
            province=location.province,
            latitude=location.lat,
            longitude=location.lng,
            timezone=location.timezone,
            population=location.population,
        )
