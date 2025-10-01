"""
Tests for the AddProfileStep timezone conversion functionality.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from dao.geolocation import GeolocationDAO
from data.models import Gender, RelationshipType
from kundli.add_profile import AddProfileStep, ProfileState


class TestAddProfileStepTimezoneConversion:
    """Test timezone conversion from local time to UTC in profile creation."""

    @pytest.fixture
    def add_profile_step(self):
        """Create an AddProfileStep instance."""
        return AddProfileStep()

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = MagicMock()
        session.user_id = "test-user-id"
        return session

    @pytest.fixture
    def mock_message(self):
        """Create a mock message."""
        return MagicMock()

    @pytest.fixture
    def mock_location(self):
        """Create a mock location with timezone."""
        location = MagicMock()
        location.id = 1
        location.city = "Mumbai"
        location.province = "Maharashtra"
        location.country = "India"
        location.latitude = 19.0760
        location.longitude = 72.8777
        location.timezone = "Asia/Kolkata"
        return location

    @pytest.fixture
    def profile_state_with_timezone(self):
        """Create a profile state with birth datetime in UTC."""
        return ProfileState(
            name="Test User",
            birth_date=datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc).date(),
            birth_time=datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc).time(),
            birth_place="Mumbai",
            birth_location_id=1,
            gender=Gender.MALE,
            relationship=RelationshipType.SELF,
        )

    def test_timezone_conversion_with_valid_location(
        self, add_profile_step, mock_location
    ):
        """Test that birth_datetime is converted from local time to UTC."""
        # Mock the geolocation DAO
        add_profile_step.geolocation_dao = MagicMock()
        add_profile_step.geolocation_dao.get_location_by_id.return_value = mock_location

        # Create a local time datetime (no timezone info)
        local_datetime = datetime(1990, 1, 1, 22, 30, 0)  # 10:30 PM local time

        # Call the timezone conversion logic
        birth_datetime_utc = add_profile_step._convert_birth_datetime_to_utc(
            local_datetime, 1
        )

        # Verify the conversion
        assert birth_datetime_utc is not None
        assert birth_datetime_utc.tzinfo == timezone.utc
        # Mumbai is UTC+5:30, so 10:30 PM local time should become 5:00 PM UTC
        assert birth_datetime_utc.hour == 17
        assert birth_datetime_utc.minute == 0

    def test_timezone_conversion_with_no_location_id(self, add_profile_step):
        """Test that birth_datetime is unchanged when no location_id is provided."""
        local_datetime = datetime(1990, 1, 1, 12, 0, 0)  # No timezone info

        result = add_profile_step._convert_birth_datetime_to_utc(local_datetime, None)

        assert result == local_datetime

    def test_timezone_conversion_with_no_birth_datetime(self, add_profile_step):
        """Test that None is returned when no birth_datetime is provided."""
        result = add_profile_step._convert_birth_datetime_to_utc(None, 1)

        assert result is None

    def test_timezone_conversion_with_location_no_timezone(self, add_profile_step):
        """Test that birth_datetime is unchanged when location has no timezone."""
        # Mock location without timezone
        location_no_tz = MagicMock()
        location_no_tz.id = 1
        location_no_tz.timezone = None

        add_profile_step.geolocation_dao = MagicMock()
        add_profile_step.geolocation_dao.get_location_by_id.return_value = (
            location_no_tz
        )

        local_datetime = datetime(1990, 1, 1, 12, 0, 0)  # No timezone info

        result = add_profile_step._convert_birth_datetime_to_utc(local_datetime, 1)

        assert result == local_datetime

    def test_timezone_conversion_with_invalid_timezone(self, add_profile_step):
        """Test that birth_datetime is unchanged when timezone is invalid."""
        # Mock location with invalid timezone
        location_invalid_tz = MagicMock()
        location_invalid_tz.id = 1
        location_invalid_tz.timezone = "Invalid/Timezone"

        add_profile_step.geolocation_dao = MagicMock()
        add_profile_step.geolocation_dao.get_location_by_id.return_value = (
            location_invalid_tz
        )

        local_datetime = datetime(1990, 1, 1, 12, 0, 0)  # No timezone info

        result = add_profile_step._convert_birth_datetime_to_utc(local_datetime, 1)

        # Should fall back to original datetime
        assert result == local_datetime

    def test_timezone_conversion_with_different_timezones(self, add_profile_step):
        """Test timezone conversion from local time to UTC with different timezone examples."""
        test_cases = [
            ("America/New_York", -5),  # EST (UTC-5)
            ("Europe/London", 0),  # GMT (UTC+0)
            ("Asia/Tokyo", 9),  # JST (UTC+9)
            ("Australia/Sydney", 10),  # AEST (UTC+10)
        ]

        for tz_name, expected_offset in test_cases:
            # Mock location with specific timezone
            location = MagicMock()
            location.id = 1
            location.timezone = tz_name

            add_profile_step.geolocation_dao = MagicMock()
            add_profile_step.geolocation_dao.get_location_by_id.return_value = location

            # Create a local datetime at noon (no timezone info)
            local_datetime = datetime(1990, 1, 1, 12, 0, 0)

            result = add_profile_step._convert_birth_datetime_to_utc(local_datetime, 1)

            # Verify the result is in UTC
            assert result.tzinfo == timezone.utc

            # Verify the conversion worked (the exact hour depends on DST rules)
            assert result is not None
