from datetime import date

from data.models import HouseSign

# Static sun sign descriptions - positive and engaging 50-word descriptions
SUN_SIGN_DESCRIPTIONS = {
    HouseSign.ARIES: "As an Aries, you're a natural-born leader with boundless energy and courage. Your fiery spirit drives you to take initiative and inspire others. You possess an adventurous heart and determination that helps you overcome any challenge. Your enthusiasm and optimism make you a magnetic presence.",
    HouseSign.TAURUS: "As a Taurus, you embody stability and reliability with your grounded nature. Your patience and persistence help you achieve your goals steadily. You have a deep appreciation for beauty and comfort, making you a wonderful friend and partner. Your loyalty and practical wisdom are truly admirable.",
    HouseSign.GEMINI: "As a Gemini, your curious mind and quick wit make you endlessly fascinating. You excel at communication and love learning new things. Your adaptability helps you connect with people from all walks of life. Your youthful energy and intellectual curiosity keep life exciting and engaging.",
    HouseSign.CANCER: "As a Cancer, your nurturing spirit and emotional intelligence make you deeply caring. You have an intuitive understanding of others' feelings and create warm, welcoming spaces. Your loyalty and protective nature make you a cherished friend and family member. Your compassion is truly special.",
    HouseSign.LEO: "As a Leo, your natural charisma and confidence light up any room you enter. Your generous heart and creative spirit inspire those around you. You have a natural ability to lead and motivate others with your warmth and enthusiasm. Your loyalty and passion make you unforgettable.",
    HouseSign.VIRGO: "As a Virgo, your attention to detail and analytical mind make you incredibly reliable. Your practical approach and helpful nature make you a valuable friend and colleague. You have a deep desire to improve and perfect, which drives you to excellence. Your kindness and wisdom are truly appreciated.",
    HouseSign.LIBRA: "As a Libra, your sense of balance and fairness makes you a natural peacemaker. Your charm and diplomacy help you navigate any situation gracefully. You have a deep appreciation for beauty and harmony in all aspects of life. Your ability to see multiple perspectives is truly valuable.",
    HouseSign.SCORPIO: "As a Scorpio, your intensity and passion give you incredible depth and insight. Your determination and resourcefulness help you achieve what you set your mind to. You have a powerful intuition and ability to understand hidden truths. Your loyalty and transformative energy are truly remarkable.",
    HouseSign.SAGITTARIUS: "As a Sagittarius, your adventurous spirit and optimistic outlook make life an exciting journey. Your wisdom and philosophical nature help you see the bigger picture. You inspire others with your enthusiasm and love for exploration. Your honesty and generosity make you a wonderful companion.",
    HouseSign.CAPRICORN: "As a Capricorn, your ambition and discipline help you achieve remarkable success. Your practical wisdom and responsible nature make you incredibly reliable. You have a strong sense of tradition and work ethic that others admire. Your patience and determination are truly inspiring.",
    HouseSign.AQUARIUS: "As an Aquarius, your innovative thinking and humanitarian spirit make you truly unique. Your independence and originality help you see possibilities others miss. You have a natural ability to connect with people and champion important causes. Your vision and progressive nature are inspiring.",
    HouseSign.PISCES: "As a Pisces, your compassionate heart and artistic soul make you deeply empathetic. Your intuition and creativity help you understand the world in beautiful ways. You have a natural ability to heal and comfort others with your gentle wisdom. Your dreamy nature and kindness are truly magical.",
}


def get_sun_sign(birth_date: date) -> HouseSign:
    """Determine sun sign based on birth date using HouseSign enum."""
    month = birth_date.month
    day = birth_date.day

    # Sun sign date ranges (month, day)
    sun_signs = {
        HouseSign.ARIES: [(3, 21), (4, 19)],
        HouseSign.TAURUS: [(4, 20), (5, 20)],
        HouseSign.GEMINI: [(5, 21), (6, 20)],
        HouseSign.CANCER: [(6, 21), (7, 22)],
        HouseSign.LEO: [(7, 23), (8, 22)],
        HouseSign.VIRGO: [(8, 23), (9, 22)],
        HouseSign.LIBRA: [(9, 23), (10, 22)],
        HouseSign.SCORPIO: [(10, 23), (11, 21)],
        HouseSign.SAGITTARIUS: [(11, 22), (12, 21)],
        HouseSign.CAPRICORN: [(12, 22), (1, 19)],
        HouseSign.AQUARIUS: [(1, 20), (2, 18)],
        HouseSign.PISCES: [(2, 19), (3, 20)],
    }

    for sign, (start, end) in sun_signs.items():
        start_month, start_day = start
        end_month, end_day = end

        # Handle Capricorn which spans across year end
        if start_month == 12:  # Capricorn
            if (month == 12 and day >= start_day) or (month == 1 and day <= end_day):
                return sign
        else:
            if (month == start_month and day >= start_day) or (
                month == end_month and day <= end_day
            ):
                return sign

    # Fallback (shouldn't happen with proper date ranges)
    return HouseSign.ARIES


def get_sun_sign_description(sun_sign: HouseSign) -> str:
    """Get the static description for a given sun sign."""
    return SUN_SIGN_DESCRIPTIONS.get(sun_sign, SUN_SIGN_DESCRIPTIONS[HouseSign.ARIES])
