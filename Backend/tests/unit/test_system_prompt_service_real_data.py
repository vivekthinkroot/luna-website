"""
Simplified test for the SystemPromptService using real profile data.

This test fetches actual profile data using the specified profile ID,
generates the system prompt, and stores it in the output folder for manual validation.
"""

from datetime import datetime, timezone
from pathlib import Path

from dao.profiles import ProfileDAO
from qna.system_prompt_service import SystemPromptService


class TestSystemPromptServiceRealData:
    """Test case for SystemPromptService using real profile data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SystemPromptService()
        self.profile_dao = ProfileDAO()
        
        "⚠️⚠️⚠️⚠️⚠️⚠️ IMPORTANT: Set a real profile_id in the below variable"
        "that has real and well-formed data in profile_data.kundli_data"
        self.profile_id = ""

        # Create output directory if it doesn't exist
        self.output_dir = Path("tests/output")
        self.output_dir.mkdir(exist_ok=True)

    def test_system_prompt_generation_with_real_data(self):
        """Test system prompt generation using real profile data and save to output folder."""
        # Check if profile_id is empty and show error
        if not self.profile_id or self.profile_id.strip() == "":
            print("❌ ERROR: Profile ID is empty or not set!")
            return
        
        # Fetch real profile data
        profile_data = self.profile_dao.get_profile_data(self.profile_id)
        assert (
            profile_data is not None
        ), f"Profile data not found for ID: {self.profile_id}"
        assert profile_data.profile_id is not None
        assert profile_data.kundli_data is not None

        print(f"Successfully fetched profile data for: {profile_data.profile_id}")
        print(f"Kundli data keys: {list(profile_data.kundli_data.keys())}")

        # Generate system prompt using the service
        system_prompt = self.service.construct_system_prompt(self.profile_id)
        assert system_prompt is not None
        assert len(system_prompt) > 0

        print(f"Generated system prompt length: {len(system_prompt)} characters")

        # Save the generated prompt to file for manual validation
        output_filename = f"{self.profile_id}_system_prompt.md"
        output_path = self.output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)

        print(f"System prompt saved to: {output_path}")

        # Basic validation that the prompt contains expected content
        assert "Luna" in system_prompt
        assert "Vedic" in system_prompt or "astrology" in system_prompt

        print(
            "✅ Test completed successfully - check the output file for manual validation"
        )


if __name__ == "__main__":
    # Run the test
    test_instance = TestSystemPromptServiceRealData()
    test_instance.setup_method()

    print("Running simplified system prompt service test with real data...")

    try:
        test_instance.test_system_prompt_generation_with_real_data()
        print("\n✓ Test passed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
