"""
Integration tests for GeolocationService

Tests the GeolocationService with real database connections to validate
actual search functionality, fuzzy matching, and location resolution.
"""

import pytest

from dao.geolocation import LocationCandidate
from services.geolocation import GeolocationService, LocationSearchResult


class TestGeolocationServiceIntegration:
    """Integration test cases for GeolocationService using real database."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GeolocationService()

    def test_search_location_exact_match_major_city(self):
        """Test location search with exact matches for major cities."""
        # Test with well-known cities that should exist in the database
        test_cities = ["Chennai", "Mumbai", "Delhi", "Bangalore", "Kolkata"]

        for city_name in test_cities:
            result = self.service.search_location(city_name)

            # Assertions
            assert isinstance(result, LocationSearchResult)
            assert result.search_term == city_name

            # Should have exact matches for major cities
            if result.total_results > 0:
                assert (
                    len(result.exact_matches) > 0
                ), f"No exact matches found for {city_name}"

                # Verify the first match has the correct city name
                first_match = result.exact_matches[0]
                assert isinstance(first_match, LocationCandidate)
                assert first_match.city.lower() == city_name.lower()
                assert first_match.latitude is not None
                assert first_match.longitude is not None
                assert first_match.id is not None

    def test_search_location_case_insensitive(self):
        """Test that search works with different case variations."""
        # Test the same city with different cases
        test_variations = [
            "chennai",  # lowercase
            "CHENNAI",  # uppercase
            "Chennai",  # title case
            "ChEnNaI",  # mixed case
        ]

        results = []
        for variation in test_variations:
            try:
                result = self.service.search_location(variation)
                results.append(result)
            except Exception as e:
                pytest.fail(f"Search failed for variation '{variation}': {e}")

        # All variations should return similar results
        if results and results[0].total_results > 0:
            first_result_count = results[0].total_results
            for i, result in enumerate(results[1:], 1):
                assert (
                    result.total_results == first_result_count
                ), f"Variation {test_variations[i]} returned different count than {test_variations[0]}"

    def test_search_location_fuzzy_matching(self):
        """Test fuzzy matching with common typos."""
        # Test common typos for well-known cities
        fuzzy_test_cases = [
            ("Chenai", "Chennai"),  # Missing 'n'
            ("Mumbay", "Mumbai"),  # 'y' instead of 'i'
            ("Deli", "Delhi"),  # Missing 'h'
            ("Bangalor", "Bangalore"),  # Missing 'e'
            ("Calcuta", "Kolkata"),  # Old spelling variation
        ]

        for typo, expected_city in fuzzy_test_cases:
            result = self.service.search_location(typo)

            assert isinstance(result, LocationSearchResult)
            assert result.search_term == typo

            # Check if we got results (either exact or fuzzy)
            total_matches = len(result.exact_matches) + len(result.fuzzy_matches)

            if total_matches > 0:
                # Check if the expected city appears in results
                found_expected = False

                # Check exact matches
                for match in result.exact_matches:
                    if match.city.lower() == expected_city.lower():
                        found_expected = True
                        break

                # Check fuzzy matches
                if not found_expected:
                    for match, score in result.fuzzy_matches:
                        if match.city.lower() == expected_city.lower():
                            found_expected = True
                            assert (
                                score > 0.0
                            ), f"Fuzzy match score should be positive for {typo} -> {expected_city}"
                            break

                if not found_expected:
                    # Print available matches for debugging
                    exact_cities = [m.city for m in result.exact_matches]
                    fuzzy_cities = [m[0].city for m in result.fuzzy_matches]
                    print(
                        f"Typo '{typo}' didn't match expected '{expected_city}'. Found exact: {exact_cities}, fuzzy: {fuzzy_cities}"
                    )

    def test_search_location_empty_input(self):
        """Test search with empty or invalid input."""
        invalid_inputs = ["", "   ", "\t", "\n"]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError, match="Location name cannot be empty"):
                self.service.search_location(invalid_input)

    def test_search_location_non_existent_place(self):
        """Test search with completely non-existent place names."""
        fake_places = ["Nonexistentville", "Fakecityburg", "Imaginationtopia"]

        for fake_place in fake_places:
            result = self.service.search_location(fake_place)

            assert isinstance(result, LocationSearchResult)
            assert result.search_term == fake_place
            # Should return no results for completely made-up places
            # (though fuzzy matching might return some low-confidence matches)

    def test_get_location_coordinates_real_data(self):
        """Test getting coordinates for actual location IDs from search results."""
        # First find a real location
        search_result = self.service.search_location("Chennai")

        if search_result.total_results > 0:
            # Get the first available location
            test_location = None
            if search_result.exact_matches:
                test_location = search_result.exact_matches[0]
            elif search_result.fuzzy_matches:
                test_location = search_result.fuzzy_matches[0][0]

            if test_location:
                # Test coordinate retrieval
                coords = self.service.get_location_coordinates(test_location.id)

                assert coords is not None
                assert len(coords) == 2
                lat, lng = coords
                assert isinstance(lat, (int, float))
                assert isinstance(lng, (int, float))
                # Basic sanity checks for coordinates
                assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
                assert -180 <= lng <= 180, f"Invalid longitude: {lng}"

                # Coordinates should match the location object
                assert abs(lat - test_location.latitude) < 0.0001
                assert abs(lng - test_location.longitude) < 0.0001

    def test_get_location_coordinates_invalid_id(self):
        """Test getting coordinates for non-existent location ID."""
        # Use a very large ID that's unlikely to exist
        invalid_id = 999999999
        coords = self.service.get_location_coordinates(invalid_id)
        assert coords is None

    def test_get_location_details_real_data(self):
        """Test getting location details for actual location IDs."""
        # First find a real location
        search_result = self.service.search_location("Mumbai")

        if search_result.total_results > 0:
            # Get the first available location
            test_location = None
            if search_result.exact_matches:
                test_location = search_result.exact_matches[0]
            elif search_result.fuzzy_matches:
                test_location = search_result.fuzzy_matches[0][0]

            if test_location:
                # Test detail retrieval
                details = self.service.get_location_details(test_location.id)

                assert details is not None
                assert isinstance(details, LocationCandidate)
                assert details.id == test_location.id
                assert details.city == test_location.city
                assert details.latitude == test_location.latitude
                assert details.longitude == test_location.longitude

    def test_get_location_details_invalid_id(self):
        """Test getting location details for non-existent location ID."""
        invalid_id = 999999999
        details = self.service.get_location_details(invalid_id)
        assert details is None

    def test_resolve_best_match_population_preference(self):
        """Test that best match resolution prefers higher population cities."""
        # Search for a common city name that might have multiple matches
        result = self.service.resolve_best_match("Chennai")

        if result is not None:
            assert isinstance(result, LocationCandidate)
            assert result.city.lower() == "chennai"

            # Find all Chennai matches to verify population preference
            search_result = self.service.search_location("Chennai")
            if len(search_result.exact_matches) > 1:
                # Sort by population and verify our result is the highest
                sorted_matches = sorted(
                    search_result.exact_matches,
                    key=lambda x: x.population or 0,
                    reverse=True,
                )
                highest_pop_match = sorted_matches[0]

                assert (
                    result.id == highest_pop_match.id
                ), "Best match should prefer location with highest population"

    def test_resolve_best_match_fuzzy_threshold(self):
        """Test that fuzzy matches below threshold are rejected."""
        # Use a very dissimilar string that should not match anything
        result = self.service.resolve_best_match("xyzabc123")

        # Should return None for strings that don't meet fuzzy threshold
        assert result is None

    def test_get_multiple_locations_real_data(self):
        """Test getting multiple location details with real IDs."""
        # First find some real location IDs
        search_results = []
        test_cities = ["Chennai", "Mumbai", "Delhi"]

        for city in test_cities:
            result = self.service.search_location(city)
            if result.total_results > 0:
                if result.exact_matches:
                    search_results.append(result.exact_matches[0])
                elif result.fuzzy_matches:
                    search_results.append(result.fuzzy_matches[0][0])

        if len(search_results) >= 2:
            # Test with first two locations
            location_ids = [loc.id for loc in search_results[:2]]

            multiple_locations = self.service.get_multiple_locations(location_ids)

            assert len(multiple_locations) == 2
            assert all(isinstance(loc, LocationCandidate) for loc in multiple_locations)

            # Verify returned IDs match requested IDs
            returned_ids = {loc.id for loc in multiple_locations}
            requested_ids = set(location_ids)
            assert returned_ids == requested_ids

    def test_normalize_location_name_functionality(self):
        """Test the actual normalization logic with real inputs."""
        # Test normalization with actual examples
        test_cases = [
            ("  chennai  ", "Chennai"),
            ("new   york", "New York"),
            ("st. petersburg", "Saint Petersburg"),
            ("mt. everest", "Mount Everest"),
            ("St Louis", "Saint Louis"),
            ("Mt Washington", "Mount Washington"),
            ("los angeles", "Los Angeles"),
        ]

        for input_name, expected in test_cases:
            result = self.service._normalize_location_name(input_name)
            assert (
                result == expected
            ), f"Expected '{expected}', got '{result}' for input '{input_name}'"

    def test_calculate_similarity_algorithm(self):
        """Test the similarity calculation with real location name pairs."""
        # Test exact matches
        assert self.service._calculate_similarity("Chennai", "Chennai") == 1.0
        assert self.service._calculate_similarity("", "") == 0.0

        # Test substring matches
        similarity = self.service._calculate_similarity("New York", "York")
        assert similarity == 0.9

        # Test common typos and their similarities
        typo_similarities = [
            ("Chennai", "Chenai", 0.7),  # Common typo
            ("Mumbai", "Mumbay", 0.7),  # Common typo
            ("Bangalore", "Bangalor", 0.8),  # Missing letter
            ("Delhi", "Deli", 0.6),  # Missing letter
        ]

        for original, typo, min_expected in typo_similarities:
            similarity = self.service._calculate_similarity(original, typo)
            assert (
                similarity >= min_expected
            ), f"Similarity between '{original}' and '{typo}' was {similarity}, expected >= {min_expected}"

        # Test very different strings
        similarity = self.service._calculate_similarity("Chennai", "xyz")
        assert similarity < 0.3, "Very different strings should have low similarity"

        # Test empty string cases
        assert self.service._calculate_similarity("", "Chennai") == 0.0
        assert self.service._calculate_similarity("Chennai", "") == 0.0

    def test_location_search_result_structure(self):
        """Test that search results have the correct structure and types."""
        result = self.service.search_location("Chennai")

        # Test result structure
        assert isinstance(result, LocationSearchResult)
        assert hasattr(result, "exact_matches")
        assert hasattr(result, "fuzzy_matches")
        assert hasattr(result, "search_term")
        assert hasattr(result, "total_results")

        assert isinstance(result.exact_matches, list)
        assert isinstance(result.fuzzy_matches, list)
        assert isinstance(result.search_term, str)
        assert isinstance(result.total_results, int)

        # Test exact matches structure
        for match in result.exact_matches:
            assert isinstance(match, LocationCandidate)
            assert hasattr(match, "id")
            assert hasattr(match, "city")
            assert hasattr(match, "latitude")
            assert hasattr(match, "longitude")

        # Test fuzzy matches structure
        for match_tuple in result.fuzzy_matches:
            assert isinstance(match_tuple, tuple)
            assert len(match_tuple) == 2
            match, score = match_tuple
            assert isinstance(match, LocationCandidate)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
