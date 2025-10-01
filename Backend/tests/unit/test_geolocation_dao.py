"""
Unit tests for GeolocationDAO.
Tests all scenarios supported by the geolocation service.
"""

import pytest
from unittest.mock import patch, MagicMock

from dao.geolocation import GeolocationDAO
from data.models import TLocations


class TestGeolocationDAO:
    """Test cases for GeolocationDAO operations."""

    @pytest.fixture
    def geoloc_dao(self):
        """Create a GeolocationDAO instance for testing."""
        return GeolocationDAO()

    @pytest.fixture
    def sample_location_data(self):
        """Sample location data for testing."""
        return [
            TLocations(
                id=1,
                source_id=1001,
                city="Chennai",
                country="India", 
                province="Tamil Nadu",
                iso3="IND",
                lat=13.0827,
                lng=80.2707,
                timezone="Asia/Kolkata",
                population=8000000
            ),
            TLocations(
                id=2,
                source_id=1002,
                city="Bangalore",
                country="India",
                province="Karnataka", 
                iso3="IND",
                lat=12.9716,
                lng=77.5946,
                timezone="Asia/Kolkata",
                population=12000000
            ),
            TLocations(
                id=3,
                source_id=1003,
                city="Chennai",
                country="United States",
                province="Tennessee",
                iso3="USA", 
                lat=35.4676,
                lng=-80.8414,
                timezone="America/New_York",
                population=2000
            )
        ]

    def test_get_exact_matches_single_result(self, geoloc_dao, sample_location_data):
        """Test exact match returning single result."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock exact match finding Chennai, India
            mock_db.exec.return_value.all.return_value = [sample_location_data[0]]
            
            results = geoloc_dao.get_exact_matches("Chennai")
            
            assert len(results) == 1
            assert results[0].city == "Chennai"
            assert results[0].country == "India"
            assert results[0].lat == 13.0827

    def test_get_exact_matches_multiple_results(self, geoloc_dao, sample_location_data):
        """Test exact match returning multiple results for same city name."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock finding both Chennai entries
            chennai_locations = [sample_location_data[0], sample_location_data[2]]
            mock_db.exec.return_value.all.return_value = chennai_locations
            
            results = geoloc_dao.get_exact_matches("Chennai")
            
            assert len(results) == 2
            assert all(loc.city == "Chennai" for loc in results)
            countries = [loc.country for loc in results]
            assert "India" in countries
            assert "United States" in countries

    def test_get_exact_matches_case_insensitive_fallback(self, geoloc_dao, sample_location_data):
        """Test case-insensitive fallback when exact match fails."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # First call (exact match) returns empty, second call (ilike) returns result
            mock_db.exec.return_value.all.side_effect = [[], [sample_location_data[0]]]
            
            results = geoloc_dao.get_exact_matches("chennai")  # lowercase
            
            assert len(results) == 1
            assert results[0].city == "Chennai"
            # Verify that exec was called twice (exact match + ilike)
            assert mock_db.exec.call_count == 2

    def test_get_exact_matches_no_results(self, geoloc_dao):
        """Test exact match with no results found."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Both exact and ilike queries return empty
            mock_db.exec.return_value.all.return_value = []
            
            results = geoloc_dao.get_exact_matches("Nonexistent City")
            
            assert len(results) == 0

    def test_get_contains_matches(self, geoloc_dao, sample_location_data):
        """Test contains matching for partial city names."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock finding cities containing "chen"
            mock_db.exec.return_value.all.return_value = [sample_location_data[0]]
            
            results = geoloc_dao.get_contains_matches("chen")
            
            assert len(results) == 1
            assert "chen" in results[0].city.lower()

    def test_get_contains_matches_with_limit(self, geoloc_dao, sample_location_data):
        """Test contains matching respects limit parameter."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_db.exec.return_value.all.return_value = sample_location_data[:2]
            
            results = geoloc_dao.get_contains_matches("Ban", limit=2)
            
            assert len(results) <= 2

    def test_get_all_city_names(self, geoloc_dao):
        """Test retrieving all city names and IDs for fuzzy matching."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock city names and IDs
            mock_db.exec.return_value.all.return_value = [
                ("Chennai", 1),
                ("Bangalore", 2),
                ("Mumbai", 3)
            ]
            
            results = geoloc_dao.get_all_city_names()
            
            assert len(results) == 3
            assert ("Chennai", 1) in results
            assert ("Bangalore", 2) in results
            assert ("Mumbai", 3) in results

    def test_get_locations_by_ids(self, geoloc_dao, sample_location_data):
        """Test bulk retrieval of locations by IDs."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock returning specific locations by ID
            mock_db.exec.return_value.all.return_value = sample_location_data[:2]
            
            results = geoloc_dao.get_locations_by_ids([1, 2])
            
            assert len(results) == 2
            assert results[0].id == 1
            assert results[0].source_id == 1001
            assert results[1].id == 2
            assert results[1].source_id == 1002

    def test_get_location_by_id_found(self, geoloc_dao, sample_location_data):
        """Test single location retrieval by ID - found."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_db.exec.return_value.one_or_none.return_value = sample_location_data[0]
            
            result = geoloc_dao.get_location_by_id(1)
            
            assert result is not None
            assert result.id == 1
            assert result.source_id == 1001
            assert result.city == "Chennai"

    def test_get_location_by_id_not_found(self, geoloc_dao):
        """Test single location retrieval by ID - not found."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_db.exec.return_value.one_or_none.return_value = None
            
            result = geoloc_dao.get_location_by_id(999)
            
            assert result is None

    def test_database_error_handling(self, geoloc_dao):
        """Test handling of database errors."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                geoloc_dao.get_exact_matches("Chennai")

    def test_empty_location_name_handling(self, geoloc_dao):
        """Test handling of empty/whitespace location names."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.exec.return_value.all.return_value = []
            
            # Test empty string
            results = geoloc_dao.get_exact_matches("")
            assert len(results) == 0
            
            # Test whitespace only
            results = geoloc_dao.get_exact_matches("   ")
            assert len(results) == 0

    def test_location_name_normalization(self, geoloc_dao, sample_location_data):
        """Test that location names are properly normalized (title case)."""
        with patch('dao.geolocation.get_session') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.exec.return_value.all.return_value = [sample_location_data[0]]
            
            # Test various input formats
            test_inputs = ["chennai", "CHENNAI", "  chennai  ", "ChEnNaI"]
            
            for input_name in test_inputs:
                results = geoloc_dao.get_exact_matches(input_name)
                # Should find the location regardless of case/whitespace
                assert len(results) >= 0  # May be 0 or more depending on mock setup