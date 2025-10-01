"""
Speech service interface for Luna.
Responsible for speech-to-text and text-to-speech transformations.
"""
from typing import Dict, Any
from abc import ABC, abstractmethod

class SpeechService(ABC):
    """Abstract base class for speech service."""

    @abstractmethod
    async def speech_to_text(self, audio_file: bytes) -> str:
        """
        Convert speech audio to text.
        Args:
            audio_file (bytes): Audio file bytes.
        Returns:
            str: Transcribed text.
        """
        pass

    @abstractmethod
    async def text_to_speech(self, text: str, voice_config: Dict[str, Any]) -> bytes:
        """
        Convert text to speech audio.
        Args:
            text (str): Text to convert.
            voice_config (Dict[str, Any]): Voice configuration parameters.
        Returns:
            bytes: Audio file bytes.
        """
        pass
