import os
import logging

logger = logging.getLogger(__name__)

class TTSConfig:
    """Unified TTS configuration management."""
    
    # Provider selection
    TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'uplift')  # 'uplift' or 'openai'
    
    # Uplift TTS Settings
    UPLIFT_API_KEY = os.getenv('UPLIFT_API_KEY')
    UPLIFT_TTS_URL = os.getenv('UPLIFT_TTS_URL', 'https://api.upliftai.org/v1/synthesis/text-to-speech')
    UPLIFT_DEFAULT_VOICE = os.getenv('UPLIFT_DEFAULT_VOICE', 'broadband-support')
    UPLIFT_OUTPUT_FORMAT = os.getenv('UPLIFT_OUTPUT_FORMAT', 'MP3_22050_128')
    UPLIFT_MAX_TEXT_LENGTH = int(os.getenv('UPLIFT_MAX_TEXT_LENGTH', '4000'))
    
    # OpenAI Fallback Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_TTS_VOICE = os.getenv('OPENAI_TTS_VOICE', 'alloy')
    OPENAI_TTS_MODEL = os.getenv('OPENAI_TTS_MODEL', 'tts-1')
    
    # Language-specific voice mapping
    # Resilient fallback checking both UPLIFT_URDU_VOICE and older env vars like UPLIFT_VOICE_ID_URDU
    VOICE_MAPPING = {
        'ur': os.getenv('UPLIFT_URDU_VOICE') or os.getenv('UPLIFT_VOICE_ID_URDU') or os.getenv('UPLIFT_ROMAN_URDU_VOICE_ID') or os.getenv('UPLIFT_DEFAULT_VOICE') or 'broadband-support',
        'en': os.getenv('UPLIFT_ENGLISH_VOICE') or os.getenv('UPLIFT_VOICE_ID_EN') or os.getenv('UPLIFT_DEFAULT_VOICE') or 'broadband-support',
        'sd': os.getenv('UPLIFT_SINDHI_VOICE') or os.getenv('UPLIFT_DEFAULT_VOICE') or 'broadband-support',
        'default': os.getenv('UPLIFT_DEFAULT_VOICE', 'broadband-support')
    }
    
    # Force Uplift for Urdu (no fallback)
    FORCE_UPLIFT_FOR_URDU = os.getenv('FORCE_UPLIFT_FOR_URDU', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate configuration and log warnings."""
        if cls.TTS_PROVIDER == 'uplift':
            if not cls.UPLIFT_API_KEY:
                logger.warning("⚠️ UPLIFT_API_KEY not set! TTS will fail.")
                return False
            logger.info("✅ Uplift TTS configured")
        elif cls.TTS_PROVIDER == 'openai':
            if not cls.OPENAI_API_KEY:
                logger.warning("⚠️ OPENAI_API_KEY not set! TTS will fail.")
                return False
            logger.info("✅ OpenAI TTS configured (fallback mode)")
        else:
            logger.warning(f"⚠️ Unknown TTS_PROVIDER: {cls.TTS_PROVIDER}")
            return False
        return True
    
    @classmethod
    def get_voice_for_language(cls, language: str) -> str:
        """Get the appropriate voice ID for a language."""
        return cls.VOICE_MAPPING.get(language, cls.VOICE_MAPPING['default'])
