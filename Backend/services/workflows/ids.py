"""
Centralized identifiers for workflow and step IDs.

Use these enums instead of string literals to avoid typos and keep
referencing consistent across the codebase.
"""

from enum import Enum


class Workflows(str, Enum):
    GENERATE_KUNDLI = "generate_kundli"
    PROFILE_QNA = "profile_qna"
    MAIN_MENU = "main_menu"
    UNKNOWN = "unknown"


class Steps(str, Enum):
    PROFILE_RESOLUTION = "profile_resolution_step"
    PROFILE_ADDITION = "profile_addition_step"
    KUNDLI_GENERATION = "kundli_generation_step"
    PROFILE_QNA_STEP = "profile_qna_step"
    MAIN_MENU_STEP = "main_menu_step"
    UNKNOWN_FALLBACK = "unknown_fallback_step"
