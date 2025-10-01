"""
Geolocation Service Module

This module provides business logic for location resolution and management.
It handles fuzzy matching, location search, and coordinate retrieval for
profile creation and Kundli generation using the cities table.
"""

from typing import List, Optional, Tuple
import re
from difflib import SequenceMatcher
from pydantic import BaseModel

from dao.cities import CitiesDAO, CityCandidate
from config.settings import get_geolocation_settings


class LocationSearchResult(BaseModel):
    """Result of a location search operation."""
    
    exact_matches: List[CityCandidate]
    fuzzy_matches: List[Tuple[CityCandidate, float]]  # (candidate, similarity_score)
    search_term: str
    total_results: int


class GeolocationService:
    """
    Service class for geolocation operations with business logic.
    
    Provides fuzzy matching, location search, and coordinate resolution
    for user birth places to support Kundli generation.
    """
    
    def __init__(self):
        self.dao = CitiesDAO()
        self.settings = get_geolocation_settings()
    
    def search_location(self, location_name: str) -> LocationSearchResult:
        """
        Search for locations by name with exact and fuzzy matching.
        
        Args:
            location_name: The location name to search for (e.g., "Chennai", "New York")
            
        Returns:
            LocationSearchResult: Contains exact matches, fuzzy matches with scores
            
        Raises:
            ValueError: If location_name is empty or invalid
        """
        if not location_name or not location_name.strip():
            raise ValueError("Location name cannot be empty")
        
        # Normalize the search term
        normalized_name = self._normalize_location_name(location_name)
        
        # Get exact matches first
        exact_matches = self.dao.get_exact_matches(normalized_name)
        
        # Get fuzzy matches if enabled and no exact matches found
        fuzzy_matches = []
        if self.settings.fuzzy_matching_enabled and len(exact_matches) == 0:
            fuzzy_matches = self._find_fuzzy_matches(normalized_name)
        
        total_results = len(exact_matches) + len(fuzzy_matches)
        
        return LocationSearchResult(
            exact_matches=exact_matches,
            fuzzy_matches=fuzzy_matches,
            search_term=location_name,
            total_results=total_results
        )
    
    def get_location_coordinates(self, location_id: int) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a specific location ID.
        
        Args:
            location_id: The ID of the location in the database
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        location = self.dao.get_city_by_id(location_id)
        if location and location.latitude is not None and location.longitude is not None:
            return (location.latitude, location.longitude)
        return None
    
    def get_location_details(self, location_id: int) -> Optional[CityCandidate]:
        """
        Get full location details for a specific location ID.
        
        Args:
            location_id: The ID of the location in the database
            
        Returns:
            CityCandidate with full details or None if not found
        """
        return self.dao.get_city_by_id(location_id)
    
    def resolve_best_match(self, location_name: str) -> Optional[CityCandidate]:
        """
        Find the single best match for a location name.
        
        This method applies business logic to determine the most likely
        location match for a given name.
        
        Args:
            location_name: The location name to resolve
            
        Returns:
            The best matching CityCandidate or None if no good match found
        """
        search_result = self.search_location(location_name)
        
        # If we have exact matches, prefer the one with highest population
        if search_result.exact_matches:
            return max(search_result.exact_matches, 
                      key=lambda x: x.population or 0)
        
        # If we have fuzzy matches, return the highest scoring one above threshold
        if search_result.fuzzy_matches:
            best_match, score = max(search_result.fuzzy_matches, key=lambda x: x[1])
            if score >= self.settings.fuzzy_match_threshold:
                return best_match
        
        return None
    
    def get_multiple_locations(self, location_ids: List[int]) -> List[CityCandidate]:
        """
        Get details for multiple location IDs.
        
        Args:
            location_ids: List of location IDs to retrieve
            
        Returns:
            List of CityCandidate objects
        """
        return self.dao.get_cities_by_ids(location_ids)
    
    def _normalize_location_name(self, name: str) -> str:
        """
        Normalize location name for consistent searching.
        
        Args:
            name: Raw location name
            
        Returns:
            Normalized location name
        """
        # Remove extra whitespace and convert to title case
        normalized = re.sub(r'\s+', ' ', name.strip()).title()
        
        # Handle common variations
        replacements = {
            'St ': 'Saint ',
            'St.': 'Saint',
            'Mt ': 'Mount ',
            'Mt.': 'Mount',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _find_fuzzy_matches(self, location_name: str) -> List[Tuple[CityCandidate, float]]:
        """
        Find fuzzy matches for a location name using similarity algorithms.
        
        Args:
            location_name: Normalized location name to search for
            
        Returns:
            List of (CityCandidate, similarity_score) tuples sorted by score
        """
        # Get all city names for fuzzy matching
        all_cities = self.dao.get_all_city_names()
        
        # Calculate similarity scores
        candidates_with_scores = []
        for city_name, city_id in all_cities:
            similarity = self._calculate_similarity(location_name, city_name)
            
            if similarity >= self.settings.fuzzy_match_threshold:
                # Get the full location details
                candidate = self.dao.get_city_by_id(city_id)
                if candidate:
                    candidates_with_scores.append((candidate, similarity))
        
        # Sort by similarity score (descending) and limit results
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        return candidates_with_scores[:self.settings.max_candidates]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Uses a combination of exact matching, substring matching, and
        sequence matching for robust fuzzy matching.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize both strings
        norm1 = text1.lower().strip()
        norm2 = text2.lower().strip()
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Check if one is a substring of the other
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Use SequenceMatcher for fuzzy matching
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost score if they start with the same characters
        if len(norm1) > 0 and len(norm2) > 0:
            if norm1[0] == norm2[0]:
                base_similarity += 0.1
            
            # Additional boost for longer common prefixes
            common_prefix_len = 0
            for i in range(min(len(norm1), len(norm2))):
                if norm1[i] == norm2[i]:
                    common_prefix_len += 1
                else:
                    break
            
            if common_prefix_len >= 3:  # At least 3 characters match
                base_similarity += 0.1
        
        return min(base_similarity, 1.0)  # Cap at 1.0