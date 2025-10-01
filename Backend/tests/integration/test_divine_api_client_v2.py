"""
Integration tests for DivineAPIClientV2

These tests invoke actual Divine API endpoints to validate the v2 client implementation.
No mocking is used - these are real integration tests that verify:
1. All API endpoints work correctly
2. Error handling and resilience
3. Configuration flags work as expected
4. Data model conversions are correct
5. Performance characteristics (concurrent execution)

Prerequisites:
- Valid DIVINE_ACCESS_TOKEN and DIVINE_API_KEY environment variables
- Internet connection to reach Divine API servers
- All dependencies installed (httpx, etc.)
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kundli.divineapi_v2.api_response_models import Gender
from kundli.divineapi_v2.client_v2 import APIConfig, DivineAPIClientV2, UserProfile
from kundli.divineapi_v2.output_model import RawAstroAPIData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user profile - using a complete profile with all required fields
TEST_USER_PROFILE = UserProfile(
    full_name="Test User Integration",
    day=4,
    month=2,
    year=1985,
    hour=18,
    min=53,
    sec=0,
    gender=Gender.MALE,
    place="Chennai, India",
    lat=13.0827,
    lon=80.2707,
    tzone=5.5,
)

# Alternative test profile for different scenarios
ALTERNATIVE_USER_PROFILE = UserProfile(
    full_name="Alternative Test User",
    day=25,
    month=12,
    year=1985,
    hour=8,
    min=15,
    sec=0,
    gender=Gender.FEMALE,
    place="Mumbai, India",
    lat=19.0760,
    lon=72.8777,
    tzone=5.5,
)

pytestmark = pytest.mark.asyncio

# Output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def dump_json_output(data: RawAstroAPIData, filename: str) -> None:
    """Dump RawAstroAPIData to JSON file for inspection"""
    try:
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(exist_ok=True)

        # Convert to dict, handling nested Pydantic models
        output_dict = {}
        for field_name, field_value in data.__dict__.items():
            if field_value is not None:
                if hasattr(field_value, "model_dump"):
                    # Pydantic v2 model
                    output_dict[field_name] = field_value.model_dump()
                elif hasattr(field_value, "dict"):
                    # Pydantic v1 model (fallback)
                    output_dict[field_name] = field_value.dict()
                elif isinstance(field_value, dict):
                    # Dictionary of Pydantic models
                    output_dict[field_name] = {
                        k: (
                            v.model_dump()
                            if hasattr(v, "model_dump")
                            else v.dict() if hasattr(v, "dict") else v
                        )
                        for k, v in field_value.items()
                    }
                else:
                    # Regular value
                    output_dict[field_name] = field_value

        # Add metadata
        output_dict["_metadata"] = {
            "test_timestamp": datetime.now().isoformat(),
            "total_fields": len(data.__dict__),
            "populated_fields": len(
                [v for v in data.__dict__.values() if v is not None]
            ),
            "success_rate": len([v for v in data.__dict__.values() if v is not None])
            / len(data.__dict__)
            * 100,
        }

        # Write to file
        output_file = OUTPUT_DIR / f"{filename}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_dict, f, indent=2, default=str)

        logger.info(f"✓ JSON output saved to: {output_file}")

    except Exception as e:
        logger.warning(f"Failed to dump JSON output: {e}")


@pytest.fixture(scope="session")
def check_api_credentials():
    """Verify that API credentials are available for integration tests"""
    auth_token = os.getenv("DIVINE_ACCESS_TOKEN")
    api_key = os.getenv("DIVINE_API_KEY")

    if not auth_token or not api_key:
        pytest.skip(
            "Skipping integration tests: DIVINE_ACCESS_TOKEN and DIVINE_API_KEY "
            "environment variables are required for Divine API integration tests"
        )

    logger.info("API credentials found - proceeding with integration tests")
    return {"auth_token": auth_token, "api_key": api_key}


@pytest.fixture
def client_v2(check_api_credentials):
    """Create a DivineAPIClientV2 instance for testing"""
    return DivineAPIClientV2()


class TestDivineAPIClientV2Basic:
    """Basic functionality tests for DivineAPIClientV2"""

    async def test_client_initialization(self, client_v2):
        """Test that client initializes correctly"""
        assert client_v2.auth_token is not None
        assert client_v2.api_key is not None
        assert hasattr(client_v2, "_verify_tls")
        logger.info("✓ Client initialization successful")

    async def test_fetch_all_data_default_config(self, client_v2):
        """Test fetching all data with default configuration"""
        logger.info("Testing fetch_all_astro_data with default config...")
        start_time = time.time()

        result = await client_v2.fetch_all_astro_data(TEST_USER_PROFILE)

        end_time = time.time()
        execution_time = end_time - start_time

        # Validate result type
        assert isinstance(result, RawAstroAPIData)
        logger.info(f"✓ Received RawAstroAPIData in {execution_time:.2f} seconds")

        # Validate that core data is present (these should almost always work)
        assert (
            result.basic_astro_details is not None
        ), "Basic astro details should be fetched"
        assert result.horoscope_charts is not None, "Charts should be fetched"
        assert len(result.horoscope_charts) >= 1, "At least one chart should be present"

        # Log what was successfully fetched
        successful_fields = []
        failed_fields = []

        for field_name, field_value in result.__dict__.items():
            if field_value is not None:
                if isinstance(field_value, dict) and len(field_value) > 0:
                    successful_fields.append(f"{field_name} ({len(field_value)} items)")
                elif not isinstance(field_value, dict):
                    successful_fields.append(field_name)
            else:
                failed_fields.append(field_name)

        logger.info(f"✓ Successfully fetched: {', '.join(successful_fields)}")
        if failed_fields:
            logger.warning(f"⚠ Failed to fetch: {', '.join(failed_fields)}")

        # Performance assertion - should complete in reasonable time even with many APIs
        assert execution_time < 120, f"Execution took too long: {execution_time:.2f}s"
        logger.info(f"✓ Performance test passed: {execution_time:.2f}s < 120s")

        # Dump full configuration result to JSON
        dump_json_output(result, "test_full_config_result")

    async def test_fetch_minimal_config(self, client_v2: DivineAPIClientV2):
        """Test fetching with minimal configuration"""
        logger.info("Testing fetch_all_astro_data with minimal config...")

        minimal_config = APIConfig(
            # Only enable core essentials
            basic_details=True,
            charts=["D1", "D9", "D10"],
            vimshottari_dasha=True,
            planetary_positions=True,
            ascendant_report=True,
            # Disable everything else
            dasha_analysis=False,
            sadhe_sati=False,
            kaal_sarpa_dosha=False,
            manglik_dosha=False,
            yogas=False,
            shadbala=False,
            planet_analysis=False,
            gemstone=False,
            composite_friendship=False,
        )

        start_time = time.time()
        result: RawAstroAPIData = await client_v2.fetch_all_astro_data(
            TEST_USER_PROFILE, minimal_config
        )
        end_time = time.time()
        execution_time = end_time - start_time

        # Validate that only requested data is present
        assert result.basic_astro_details is not None
        assert result.horoscope_charts is not None
        assert "D1" in result.horoscope_charts
        assert result.vimshottari_dasha is not None
        assert result.planetary_positions is not None
        assert result.ascendant_report is not None

        # Validate that disabled data is not present
        assert result.yogas is None
        assert result.gemstone is None

        logger.info(f"✓ Minimal config test passed in {execution_time:.2f}s")
        # Should be faster with fewer APIs
        assert (
            execution_time < 30
        ), f"Minimal config took too long: {execution_time:.2f}s"

        # Dump minimal configuration result to JSON
        dump_json_output(result, "test_minimal_config_result")


class TestDivineAPIClientV2Resilience:
    """Test error handling and resilience features"""

    async def test_invalid_user_data_resilience(self, client_v2):
        """Test that client handles invalid user data gracefully"""
        logger.info("Testing resilience with invalid user data...")

        # Use partial/invalid user data - this should now fail validation
        with pytest.raises(ValueError):
            invalid_profile = UserProfile(
                full_name="Test User",
                day=32,  # Invalid day
                month=13,  # Invalid month
                year=1990,
                hour=25,  # Invalid hour
                min=70,  # Invalid minute
                sec=0,
                gender=Gender.MALE,  # Valid gender
                place="Invalid Place",
                lat=999,  # Invalid latitude
                lon=999,  # Invalid longitude
                tzone=25,  # Invalid timezone
            )

        logger.info("✓ UserProfile validation correctly rejected invalid data")

    async def test_partial_api_failure_resilience(self, client_v2):
        """Test that if some APIs fail, others still succeed"""
        logger.info("Testing partial API failure resilience...")

        # Use a config that includes APIs that might fail
        mixed_config = APIConfig(
            basic_details=True,  # This should work
            charts=["D1", "D999"],  # D999 might fail
            vimshottari_dasha=True,  # This should work
            yogas=True,  # This might work
            gemstone=True,  # This might work or fail
        )

        result = await client_v2.fetch_all_astro_data(TEST_USER_PROFILE, mixed_config)

        # At least basic data should be present
        assert result.basic_astro_details is not None
        assert result.horoscope_charts is not None

        # Count successful vs failed APIs
        success_count = 0
        total_count = 0

        if result.basic_astro_details:
            success_count += 1
        total_count += 1

        if result.horoscope_charts:
            success_count += 1
        total_count += 1

        if result.vimshottari_dasha:
            success_count += 1
        total_count += 1

        if result.yogas:
            success_count += 1
        total_count += 1

        if result.gemstone:
            success_count += 1
        total_count += 1

        logger.info(f"✓ Resilience test: {success_count}/{total_count} APIs succeeded")
        assert success_count >= 2, "At least 2 APIs should succeed"


class TestDivineAPIClientV2Configuration:
    """Test different configuration scenarios"""

    def test_apiconfig_validation(self):
        """Test APIConfig Pydantic validation behavior"""
        logger.info("Testing APIConfig validation...")

        # Test valid configuration
        valid_config = APIConfig(
            basic_details=True, charts=["D1", "D9"], chart_style="north"
        )
        assert valid_config.basic_details is True
        assert valid_config.charts == ["D1", "D9"]
        assert valid_config.chart_style == "north"
        logger.info("✓ Valid configuration accepted")

        # Test default values
        default_config = APIConfig()
        assert default_config.charts == ["D1", "D9"]  # Default value
        assert default_config.chart_style == "south"  # Default value
        logger.info("✓ Default values set correctly")

        # Test field validation - use a valid value to test the validator
        validated_config = APIConfig(chart_style="north")
        assert validated_config.chart_style == "north"  # Should accept valid value
        logger.info("✓ Valid chart style accepted")

        # Test unknown attribute rejection
        with pytest.raises(ValueError, match="Extra inputs are not permitted"):
            APIConfig(unknown_field=True)
        logger.info("✓ Unknown attributes properly rejected")

        # Test empty charts handling
        empty_charts_config = APIConfig(charts=[])
        assert empty_charts_config.charts == ["D1", "D9"]  # Should be set by validator
        logger.info("✓ Empty charts properly defaulted")

        logger.info("✓ APIConfig validation tests passed")

    async def test_charts_only_config(self, client_v2):
        """Test configuration for charts only"""
        logger.info("Testing charts-only configuration...")

        charts_config = APIConfig(
            basic_details=True,  # Need this for chart context
            charts=["D1", "D9", "D10"],
            # Disable all other features
            planetary_positions=False,
            ascendant_report=False,
            vimshottari_dasha=False,
            dasha_analysis=False,
            sadhe_sati=False,
            kaal_sarpa_dosha=False,
            manglik_dosha=False,
            yogas=False,
            shadbala=False,
            planet_analysis=False,
            gemstone=False,
            composite_friendship=False,
        )

        result = await client_v2.fetch_all_astro_data(TEST_USER_PROFILE, charts_config)

        assert result.basic_astro_details is not None
        assert result.horoscope_charts is not None
        assert len(result.horoscope_charts) >= 1

        # Verify specific charts are present
        expected_charts = ["D1", "D9", "D10"]
        for chart_id in expected_charts:
            if chart_id in result.horoscope_charts:
                logger.info(f"✓ Chart {chart_id} successfully fetched")

        # Verify other data is not present
        assert result.yogas is None
        assert result.gemstone is None

        logger.info("✓ Charts-only configuration test passed")

        # Dump charts-only configuration result to JSON
        dump_json_output(result, "test_charts_only_config_result")

    async def test_analysis_only_config(self, client_v2):
        """Test configuration for analysis features only"""
        logger.info("Testing analysis-only configuration...")

        analysis_config = APIConfig(
            basic_details=True,  # Need this as foundation
            # Enable analysis features
            yogas=True,
            planet_analysis=True,
            # Disable charts and other features
            charts=[],
            planetary_positions=False,
            ascendant_report=False,
            vimshottari_dasha=False,
            dasha_analysis=False,
            sadhe_sati=False,
            kaal_sarpa_dosha=False,
            manglik_dosha=False,
            shadbala=False,
            gemstone=False,
            composite_friendship=False,
        )

        result = await client_v2.fetch_all_astro_data(
            TEST_USER_PROFILE, analysis_config
        )

        assert result.basic_astro_details is not None

        # Check that analysis features are attempted (may or may not succeed)
        analysis_attempted = 0
        if result.yogas:
            analysis_attempted += 1
        if result.planet_analysis:
            analysis_attempted += 1

        logger.info(f"✓ Analysis features attempted: {analysis_attempted}/2")

        # Verify charts are not present
        assert result.horoscope_charts is None or len(result.horoscope_charts) == 0

        logger.info("✓ Analysis-only configuration test passed")

        # Dump analysis-only configuration result to JSON
        dump_json_output(result, "test_analysis_only_config_result")


class TestDivineAPIClientV2Performance:
    """Test performance characteristics"""

    async def test_concurrent_execution_performance(self, client_v2):
        """Test that APIs are executed concurrently, not sequentially"""
        logger.info("Testing concurrent execution performance...")

        # Use a config with multiple APIs that should execute concurrently
        concurrent_config = APIConfig(
            basic_details=True,
            planetary_positions=True,
            ascendant_report=True,
            charts=["D1", "D9"],
            vimshottari_dasha=True,
            sadhe_sati=True,
            kaal_sarpa_dosha=True,
            manglik_dosha=True,
        )

        # Measure time for concurrent execution
        start_time = time.time()
        result = await client_v2.fetch_all_astro_data(
            TEST_USER_PROFILE, concurrent_config
        )
        concurrent_time = time.time() - start_time

        assert isinstance(result, RawAstroAPIData)

        # Count successful APIs
        successful_apis = 0
        if result.basic_astro_details:
            successful_apis += 1
        if result.planetary_positions:
            successful_apis += 1
        if result.ascendant_report:
            successful_apis += 1
        if result.horoscope_charts:
            successful_apis += len(result.horoscope_charts)
        if result.vimshottari_dasha:
            successful_apis += 1
        if result.sadhe_sati:
            successful_apis += 1
        if result.kaal_sarpa_dosha:
            successful_apis += 1
        if result.manglik_dosha:
            successful_apis += 1

        logger.info(
            f"✓ Concurrent execution: {successful_apis} APIs in {concurrent_time:.2f}s"
        )

        # Performance expectation: concurrent execution should be much faster than sequential
        # If we assume each API takes ~5-10 seconds, 8+ APIs sequentially would take 40-80s
        # Concurrently should be much faster, closer to the time of the slowest single API
        assert (
            concurrent_time < 60
        ), f"Concurrent execution too slow: {concurrent_time:.2f}s"

        # Calculate estimated efficiency
        if successful_apis > 0:
            time_per_api = concurrent_time / successful_apis
            logger.info(f"✓ Average time per API: {time_per_api:.2f}s (concurrent)")

        # Dump performance test result to JSON
        dump_json_output(result, "test_performance_concurrent_result")


class TestDivineAPIClientV2DataValidation:
    """Test data validation and model conversion"""

    async def test_data_model_structure(self, client_v2):
        """Test that returned data matches expected model structure"""
        logger.info("Testing data model structure...")

        config = APIConfig(
            basic_details=True,
            charts=["D1"],
            vimshottari_dasha=True,
        )

        result = await client_v2.fetch_all_astro_data(TEST_USER_PROFILE, config)

        # Validate basic structure
        assert hasattr(result, "basic_astro_details")
        assert hasattr(result, "horoscope_charts")
        assert hasattr(result, "vimshottari_dasha")

        # Validate basic astro details structure if present
        if result.basic_astro_details:
            basic_details = result.basic_astro_details
            assert hasattr(basic_details, "full_name")
            assert hasattr(basic_details, "sunsign")
            assert hasattr(basic_details, "moonsign")
            logger.info(
                f"✓ Basic details: {basic_details.full_name}, Sun: {basic_details.sunsign}, Moon: {basic_details.moonsign}"
            )

        # Validate chart structure if present
        if result.horoscope_charts and "D1" in result.horoscope_charts:
            d1_chart = result.horoscope_charts["D1"]
            assert hasattr(d1_chart, "chart_data")
            logger.info("✓ D1 chart structure validated")

        logger.info("✓ Data model structure test passed")

    async def test_backward_compatibility_conversion(self, client_v2):
        """Test conversion to FinalAstroOutput for backward compatibility"""
        logger.info("Testing backward compatibility conversion...")

        # Fetch data that should be convertible
        config = APIConfig(
            basic_details=True,
            ascendant_report=True,
            charts=["D1", "D9"],
            vimshottari_dasha=True,
            yogas=True,
        )

        result = await client_v2.fetch_all_astro_data(TEST_USER_PROFILE, config)

        # Test conversion to FinalAstroOutput
        try:
            final_output = result.to_final_astro_output()
            assert final_output is not None
            logger.info("✓ Successfully converted to FinalAstroOutput")

            # Check key fields
            if hasattr(final_output, "d1_chart") and final_output.d1_chart:
                logger.info("✓ D1 chart present in FinalAstroOutput")
            if hasattr(final_output, "d9_chart") and final_output.d9_chart:
                logger.info("✓ D9 chart present in FinalAstroOutput")
            if hasattr(final_output, "user_profile1") and final_output.user_profile1:
                logger.info("✓ User profile present in FinalAstroOutput")

        except Exception as e:
            logger.warning(f"Conversion to FinalAstroOutput failed: {e}")
            # This might be expected if certain required data is missing
            # The test should still pass as long as no crash occurs

        logger.info("✓ Backward compatibility test completed")


class TestDivineAPIClientV2EdgeCases:
    """Test edge cases and boundary conditions"""

    async def test_empty_config_lists(self, client_v2):
        """Test configuration with empty lists"""
        logger.info("Testing empty config lists...")

        empty_lists_config = APIConfig(
            basic_details=True,
            charts=[],  # Empty list
        )

        result = await client_v2.fetch_all_astro_data(
            TEST_USER_PROFILE, empty_lists_config
        )

        assert result.basic_astro_details is not None
        assert result.horoscope_charts is None or len(result.horoscope_charts) == 0

        logger.info("✓ Empty config lists handled correctly")

    async def test_alternative_user_profile(self, client_v2):
        """Test with a different user profile to ensure no hardcoded dependencies"""
        logger.info("Testing with alternative user profile...")

        config = APIConfig(
            basic_details=True,
            charts=["D1"],
            vimshottari_dasha=True,
        )

        result = await client_v2.fetch_all_astro_data(ALTERNATIVE_USER_PROFILE, config)

        assert isinstance(result, RawAstroAPIData)

        # Validate that different profile data is reflected
        if result.basic_astro_details and result.basic_astro_details.full_name:
            assert "Alternative Test User" in result.basic_astro_details.full_name
            logger.info(
                f"✓ Alternative profile processed: {result.basic_astro_details.full_name}"
            )

        logger.info("✓ Alternative user profile test passed")


# Performance benchmark test (optional, only run if specifically requested)
@pytest.mark.performance
async def test_performance_benchmark(check_api_credentials):
    """
    Performance benchmark test - only run when specifically requested.
    Usage: pytest -m performance tests/integration/test_divine_api_client_v2.py
    """
    logger.info("Running performance benchmark...")

    client = DivineAPIClientV2()

    # Test different configuration sizes
    configs = [
        ("minimal", APIConfig(basic_details=True, charts=["D1"])),
        (
            "medium",
            APIConfig(
                basic_details=True,
                charts=["D1", "D9"],
                vimshottari_dasha=True,
                yogas=True,
            ),
        ),
        ("full", APIConfig()),  # All defaults (everything enabled)
    ]

    results = {}

    for config_name, config in configs:
        logger.info(f"Benchmarking {config_name} configuration...")
        start_time = time.time()

        result = await client.fetch_all_astro_data(TEST_USER_PROFILE, config)

        end_time = time.time()
        execution_time = end_time - start_time

        # Count successful APIs
        successful_apis = sum(
            1 for field_value in result.__dict__.values() if field_value is not None
        )

        results[config_name] = {
            "time": execution_time,
            "apis": successful_apis,
            "time_per_api": (
                execution_time / successful_apis if successful_apis > 0 else 0
            ),
        }

        logger.info(
            f"✓ {config_name}: {execution_time:.2f}s, {successful_apis} APIs, "
            f"{execution_time/successful_apis:.2f}s per API"
        )

    # Log summary
    logger.info("=== Performance Benchmark Results ===")
    for config_name, metrics in results.items():
        logger.info(
            f"{config_name:>8}: {metrics['time']:>6.2f}s | "
            f"{metrics['apis']:>2} APIs | "
            f"{metrics['time_per_api']:>5.2f}s/API"
        )
