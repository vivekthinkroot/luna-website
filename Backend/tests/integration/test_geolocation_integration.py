"""
Integration tests for GeolocationService

This module contains integration tests that verify the complete workflow
of the geolocation service with real database interactions.

Note: These tests require the locations table to be populated with data.
Run only when the database is set up with location data.
"""

import pytest
from services.geolocation import GeolocationService


class TestGeolocationIntegration:
    """Integration tests for GeolocationService with database."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.geo_service = GeolocationService()
    
    @pytest.mark.integration
    def test_exact_location_search(self):
        """Test exact location search with real database."""
        # Test with a common city that should exist
        result = self.geo_service.search_location("Chennai")
        
        assert result.search_term == "Chennai"
        assert result.total_results > 0
        
        if result.exact_matches:
            match = result.exact_matches[0]
            assert match.city == "Chennai"
            assert match.latitude is not None
            assert match.longitude is not None
            assert match.country is not None
    
    @pytest.mark.integration
    def test_fuzzy_location_search(self):
        """Test fuzzy matching with real database."""
        # Test with a typo that should fuzzy match
        result = self.geo_service.search_location("Chenai")  # Typo for Chennai
        
        assert result.search_term == "Chenai"
        
        # Should find fuzzy matches if no exact matches
        if len(result.exact_matches) == 0:
            assert len(result.fuzzy_matches) > 0
            best_match, score = result.fuzzy_matches[0]
            assert score > 0.6  # Should have good similarity
    
    @pytest.mark.integration
    def test_best_match_resolution(self):
        """Test best match resolution logic."""
        # Test with a city that should have matches
        best_match = self.geo_service.resolve_best_match("Mumbai")
        
        if best_match:  # Only test if data exists
            assert best_match.city is not None
            assert best_match.latitude is not None
            assert best_match.longitude is not None
            assert best_match.id is not None
    
    @pytest.mark.integration
    def test_coordinate_retrieval(self):
        """Test coordinate retrieval for existing location."""
        # First find a location
        best_match = self.geo_service.resolve_best_match("Delhi")
        
        if best_match:  # Only test if data exists
            # Then get coordinates
            coords = self.geo_service.get_location_coordinates(best_match.id)
            
            assert coords is not None
            lat, lng = coords
            assert isinstance(lat, float)
            assert isinstance(lng, float)
            assert -90 <= lat <= 90  # Valid latitude range
            assert -180 <= lng <= 180  # Valid longitude range
    
    @pytest.mark.integration
    def test_location_details_retrieval(self):
        """Test full location details retrieval."""
        # First find a location
        best_match = self.geo_service.resolve_best_match("Bangalore")
        
        if best_match:  # Only test if data exists
            # Get full details
            details = self.geo_service.get_location_details(best_match.id)
            
            assert details is not None
            assert details.id == best_match.id
            assert details.city is not None
            assert details.latitude is not None
            assert details.longitude is not None
    
    @pytest.mark.integration
    def test_multiple_locations_retrieval(self):
        """Test retrieving multiple locations by IDs."""
        # Find some locations first
        chennai_result = self.geo_service.resolve_best_match("Chennai")
        mumbai_result = self.geo_service.resolve_best_match("Mumbai")
        
        location_ids = []
        if chennai_result:
            location_ids.append(chennai_result.id)
        if mumbai_result:
            location_ids.append(mumbai_result.id)
        
        if location_ids:  # Only test if we found locations
            locations = self.geo_service.get_multiple_locations(location_ids)
            
            assert len(locations) == len(location_ids)
            for location in locations:
                assert location.id in location_ids
                assert location.city is not None
    
    @pytest.mark.integration
    def test_profile_creation_workflow(self):
        """Test the complete workflow for profile creation."""
        # Simulate user input
        user_birth_place = "New Delhi"
        
        # Step 1: Resolve location
        best_match = self.geo_service.resolve_best_match(user_birth_place)
        
        if best_match:  # Only test if data exists
            # Step 2: Verify we can get coordinates for Kundli
            coords = self.geo_service.get_location_coordinates(best_match.id)
            
            assert coords is not None
            lat, lng = coords
            
            # Step 3: Simulate profile creation data
            profile_data = {
                "birth_place": user_birth_place,  # Original user input
                "birth_location_id": best_match.id,  # Resolved location ID
                "latitude": lat,  # For Kundli calculation
                "longitude": lng   # For Kundli calculation
            }
            
            # Verify all required data is present
            assert profile_data["birth_place"] == user_birth_place
            assert profile_data["birth_location_id"] is not None
            assert profile_data["latitude"] is not None
            assert profile_data["longitude"] is not None
            
            print(f"✅ Successfully resolved '{user_birth_place}' to {best_match.city}, {best_match.country}")
            print(f"✅ Coordinates: ({lat}, {lng}) ready for Kundli generation")
    
    @pytest.mark.integration
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty string
        with pytest.raises(ValueError):
            self.geo_service.search_location("")
        
        # Test with non-existent location ID
        coords = self.geo_service.get_location_coordinates(999999)
        assert coords is None
        
        details = self.geo_service.get_location_details(999999)
        assert details is None
        
        # Test with very obscure location
        result = self.geo_service.search_location("NonExistentCityXYZ123")
        # Should not crash, but may have no results
        assert result.search_term == "NonExistentCityXYZ123"


def main():
    """
    Manual test runner for integration tests.
    
    This can be run directly to test the geolocation service
    without pytest, useful for debugging and development.
    """
    print("=== GeolocationService Integration Tests ===\n")
    
    try:
        test_instance = TestGeolocationIntegration()
        test_instance.setup_method()
        
        print("1. Testing exact location search...")
        test_instance.test_exact_location_search()
        print("   ✅ Passed\n")
        
        print("2. Testing fuzzy location search...")
        test_instance.test_fuzzy_location_search()
        print("   ✅ Passed\n")
        
        print("3. Testing best match resolution...")
        test_instance.test_best_match_resolution()
        print("   ✅ Passed\n")
        
        print("4. Testing coordinate retrieval...")
        test_instance.test_coordinate_retrieval()
        print("   ✅ Passed\n")
        
        print("5. Testing profile creation workflow...")
        test_instance.test_profile_creation_workflow()
        print("   ✅ Passed\n")
        
        print("6. Testing edge cases...")
        test_instance.test_edge_cases()
        print("   ✅ Passed\n")
        
        print("=== All Integration Tests Passed! ===")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print("Note: These tests require the locations table to be populated with data.")


if __name__ == "__main__":
    main()