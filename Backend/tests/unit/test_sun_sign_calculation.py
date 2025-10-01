from datetime import date


from data.models import HouseSign
from kundli.utils import get_sun_sign


class TestSunSignCalculation:
    def test_aries_dates(self):
        """Test Aries dates (March 21 - April 19)"""
        assert get_sun_sign(date(2024, 3, 21)) == HouseSign.ARIES
        assert get_sun_sign(date(2024, 4, 19)) == HouseSign.ARIES
        assert get_sun_sign(date(2024, 4, 1)) == HouseSign.ARIES
        # Boundary tests
        assert get_sun_sign(date(2024, 3, 20)) != HouseSign.ARIES
        assert get_sun_sign(date(2024, 4, 20)) != HouseSign.ARIES

    def test_taurus_dates(self):
        """Test Taurus dates (April 20 - May 20)"""
        assert get_sun_sign(date(2024, 4, 20)) == HouseSign.TAURUS
        assert get_sun_sign(date(2024, 5, 20)) == HouseSign.TAURUS
        assert get_sun_sign(date(2024, 5, 1)) == HouseSign.TAURUS

    def test_gemini_dates(self):
        """Test Gemini dates (May 21 - June 20)"""
        assert get_sun_sign(date(2024, 5, 21)) == HouseSign.GEMINI
        assert get_sun_sign(date(2024, 6, 20)) == HouseSign.GEMINI
        assert get_sun_sign(date(2024, 6, 1)) == HouseSign.GEMINI

    def test_cancer_dates(self):
        """Test Cancer dates (June 21 - July 22)"""
        assert get_sun_sign(date(2024, 6, 21)) == HouseSign.CANCER
        assert get_sun_sign(date(2024, 7, 22)) == HouseSign.CANCER
        assert get_sun_sign(date(2024, 7, 1)) == HouseSign.CANCER

    def test_leo_dates(self):
        """Test Leo dates (July 23 - August 22)"""
        assert get_sun_sign(date(2024, 7, 23)) == HouseSign.LEO
        assert get_sun_sign(date(2024, 8, 22)) == HouseSign.LEO
        assert get_sun_sign(date(2024, 8, 1)) == HouseSign.LEO

    def test_virgo_dates(self):
        """Test Virgo dates (August 23 - September 22)"""
        assert get_sun_sign(date(2024, 8, 23)) == HouseSign.VIRGO
        assert get_sun_sign(date(2024, 9, 22)) == HouseSign.VIRGO
        assert get_sun_sign(date(2024, 9, 1)) == HouseSign.VIRGO

    def test_libra_dates(self):
        """Test Libra dates (September 23 - October 22)"""
        assert get_sun_sign(date(2024, 9, 23)) == HouseSign.LIBRA
        assert get_sun_sign(date(2024, 10, 22)) == HouseSign.LIBRA
        assert get_sun_sign(date(2024, 10, 1)) == HouseSign.LIBRA

    def test_scorpio_dates(self):
        """Test Scorpio dates (October 23 - November 21)"""
        assert get_sun_sign(date(2024, 10, 23)) == HouseSign.SCORPIO
        assert get_sun_sign(date(2024, 11, 21)) == HouseSign.SCORPIO
        assert get_sun_sign(date(2024, 11, 1)) == HouseSign.SCORPIO

    def test_sagittarius_dates(self):
        """Test Sagittarius dates (November 22 - December 21)"""
        assert get_sun_sign(date(2024, 11, 22)) == HouseSign.SAGITTARIUS
        assert get_sun_sign(date(2024, 12, 21)) == HouseSign.SAGITTARIUS
        assert get_sun_sign(date(2024, 12, 1)) == HouseSign.SAGITTARIUS

    def test_capricorn_dates(self):
        """Test Capricorn dates (December 22 - January 19) - spans year end"""
        assert get_sun_sign(date(2024, 12, 22)) == HouseSign.CAPRICORN
        assert get_sun_sign(date(2024, 12, 31)) == HouseSign.CAPRICORN
        assert get_sun_sign(date(2025, 1, 1)) == HouseSign.CAPRICORN
        assert get_sun_sign(date(2025, 1, 19)) == HouseSign.CAPRICORN
        # Boundary tests
        assert get_sun_sign(date(2024, 12, 21)) != HouseSign.CAPRICORN
        assert get_sun_sign(date(2025, 1, 20)) != HouseSign.CAPRICORN

    def test_aquarius_dates(self):
        """Test Aquarius dates (January 20 - February 18)"""
        assert get_sun_sign(date(2024, 1, 20)) == HouseSign.AQUARIUS
        assert get_sun_sign(date(2024, 2, 18)) == HouseSign.AQUARIUS
        assert get_sun_sign(date(2024, 2, 1)) == HouseSign.AQUARIUS

    def test_pisces_dates(self):
        """Test Pisces dates (February 19 - March 20)"""
        assert get_sun_sign(date(2024, 2, 19)) == HouseSign.PISCES
        assert get_sun_sign(date(2024, 3, 20)) == HouseSign.PISCES
        assert get_sun_sign(date(2024, 3, 1)) == HouseSign.PISCES

    def test_all_signs_covered(self):
        """Test that all 12 signs are properly defined"""
        # Test a sample date for each sign to ensure all are covered
        test_dates = [
            (date(2024, 4, 1), HouseSign.ARIES),
            (date(2024, 5, 1), HouseSign.TAURUS),
            (date(2024, 6, 1), HouseSign.GEMINI),
            (date(2024, 7, 1), HouseSign.CANCER),
            (date(2024, 8, 1), HouseSign.LEO),
            (date(2024, 9, 1), HouseSign.VIRGO),
            (date(2024, 10, 1), HouseSign.LIBRA),
            (date(2024, 11, 1), HouseSign.SCORPIO),
            (date(2024, 12, 1), HouseSign.SAGITTARIUS),
            (date(2024, 12, 25), HouseSign.CAPRICORN),
            (date(2024, 2, 1), HouseSign.AQUARIUS),
            (date(2024, 3, 1), HouseSign.PISCES),
        ]

        for test_date, expected_sign in test_dates:
            assert get_sun_sign(test_date) == expected_sign
