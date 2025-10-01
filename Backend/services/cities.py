"""
Cities Service Module

This module provides optimized business logic for city resolution and management.
It handles fuzzy matching, city search, and coordinate retrieval for
profile creation and Kundli generation using the pgAdmin cities table.
"""

from typing import List, Optional, Tuple
import re
from difflib import SequenceMatcher
from pydantic import BaseModel

from dao.cities import CitiesDAO, CityCandidate
from config.settings import get_geolocation_settings


class CitySearchResult(BaseModel):
    """Result of a city search operation."""
    
    exact_matches: List[CityCandidate]
    fuzzy_matches: List[Tuple[CityCandidate, float]]  # (candidate, similarity_score)
    search_term: str
    total_results: int


class CitiesService:
    """
    Service class for cities operations with optimized business logic.
    
    Provides fuzzy matching, city search, and coordinate resolution
    for user birth places using the pgAdmin cities table.
    """
    
    def __init__(self):
        self.dao = CitiesDAO()
        self.settings = get_geolocation_settings()
    
    def search_city(self, city_name: str) -> CitySearchResult:
        """
        Search for cities by name with exact and fuzzy matching.
        
        Args:
            city_name: The city name to search for (e.g., "Mumbai", "New York")
            
        Returns:
            CitySearchResult: Contains exact matches, fuzzy matches with scores
            
        Raises:
            ValueError: If city_name is empty or invalid
        """
        if not city_name or not city_name.strip():
            raise ValueError("City name cannot be empty")
        
        # Normalize the search term
        normalized_name = self._normalize_city_name(city_name)
        
        # Get exact matches first
        exact_matches = self.dao.get_exact_matches(normalized_name)
        
        # Get fuzzy matches if enabled and no exact matches found
        fuzzy_matches = []
        if self.settings.fuzzy_matching_enabled and len(exact_matches) == 0:
            fuzzy_matches = self._find_fuzzy_matches(normalized_name)
        
        total_results = len(exact_matches) + len(fuzzy_matches)
        
        return CitySearchResult(
            exact_matches=exact_matches,
            fuzzy_matches=fuzzy_matches,
            search_term=city_name,
            total_results=total_results
        )
    
    def get_city_coordinates(self, city_id: int) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a specific city ID.
        
        Args:
            city_id: The ID of the city in the database
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        city = self.dao.get_city_by_id(city_id)
        if city and city.latitude is not None and city.longitude is not None:
            return (city.latitude, city.longitude)
        return None
    
    def get_city_details(self, city_id: int) -> Optional[CityCandidate]:
        """
        Get full city details for a specific city ID.
        
        Args:
            city_id: The ID of the city in the database
            
        Returns:
            CityCandidate with full details or None if not found
        """
        return self.dao.get_city_by_id(city_id)
    
    def resolve_best_match(self, city_name: str) -> Optional[CityCandidate]:
        """
        Find the single best match for a city name.
        
        This method applies business logic to determine the most likely
        city match for a given name.
        
        Args:
            city_name: The city name to resolve
            
        Returns:
            The best matching CityCandidate or None if no good match found
        """
        search_result = self.search_city(city_name)
        
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
    
    def get_multiple_cities(self, city_ids: List[int]) -> List[CityCandidate]:
        """
        Get details for multiple city IDs.
        
        Args:
            city_ids: List of city IDs to retrieve
            
        Returns:
            List of CityCandidate objects
        """
        return self.dao.get_cities_by_ids(city_ids)
    
    def search_cities_optimized(self, search_term: str, limit: int = 20) -> List[CityCandidate]:
        """
        Optimized city search using the best algorithms for performance.
        
        This method uses multiple search strategies in order of preference:
        1. Exact match
        2. Case-insensitive exact match
        3. Starts with search
        4. Contains search
        
        Args:
            search_term: The search term to look for
            limit: Maximum number of results to return
            
        Returns:
            List of CityCandidate objects sorted by relevance
        """
        return self.dao.search_cities_optimized(search_term, limit)
    
    def get_cities_by_country(self, country: str, limit: int = 50) -> List[CityCandidate]:
        """
        Get cities by country.
        
        Args:
            country: Country name to search for
            limit: Maximum number of results
            
        Returns:
            List of CityCandidate objects
        """
        return self.dao.get_cities_by_country(country, limit)
    
    def get_popular_cities(self, limit: int = 20) -> List[CityCandidate]:
        """
        Get most popular cities (by population).
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of CityCandidate objects sorted by population
        """
        return self.dao.get_popular_cities(limit)
    
    def _normalize_city_name(self, name: str) -> str:
        """
        Normalize city name for consistent searching.
        
        Args:
            name: Raw city name
            
        Returns:
            Normalized city name
        """
        # Remove extra whitespace and convert to title case
        normalized = re.sub(r'\s+', ' ', name.strip()).title()
        
        # Handle common variations
        replacements = {
            'St ': 'Saint ',
            'St.': 'Saint',
            'Mt ': 'Mount ',
            'Mt.': 'Mount',
            'New ': 'New ',
            'Old ': 'Old ',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _find_fuzzy_matches(self, city_name: str) -> List[Tuple[CityCandidate, float]]:
        """
        Find fuzzy matches for a city name using similarity algorithms.
        
        Args:
            city_name: Normalized city name to search for
            
        Returns:
            List of (CityCandidate, similarity_score) tuples sorted by score
        """
        # Get all city names for fuzzy matching
        all_cities = self.dao.get_all_city_names()
        
        # Calculate similarity scores
        candidates_with_scores = []
        for city_name_db, city_id in all_cities:
            similarity = self._calculate_similarity(city_name, city_name_db)
            
            if similarity >= self.settings.fuzzy_match_threshold:
                # Get the full city details
                candidate = self.dao.get_city_by_id(city_id)
                if candidate:
                    candidates_with_scores.append((candidate, similarity))
        
        # Sort by similarity score (descending) and limit results
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        return candidates_with_scores[:self.settings.max_candidates]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using advanced algorithms.
        
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
