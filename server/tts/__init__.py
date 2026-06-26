"""
TTS package for LLM Moderator.
Supports Uplift AI TTS and OpenAI fallback.
"""

from .uplift import UpliftTTS
from .language import detect_language, get_voice_for_language
from .tts_manager import TTSManager

__all__ = [
    'UpliftTTS',
    'detect_language',
    'get_voice_for_language',
    'TTSManager'
]
