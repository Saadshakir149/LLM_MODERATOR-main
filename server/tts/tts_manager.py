import logging
from typing import Optional

from config import TTSConfig
from tts.language import detect_language, get_voice_for_language, should_use_uplift

logger = logging.getLogger(__name__)

class TTSManager:
    """
    TTS manager with provider chain and fallback.
    """
    
    def __init__(self):
        self.uplift = None
        self.openai = None
        
        # Initialize Uplift
        if TTSConfig.UPLIFT_API_KEY:
            try:
                from tts.uplift import uplift_tts
                self.uplift = uplift_tts
                logger.info("✅ Uplift TTS loaded")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load Uplift TTS: {e}")
        
        # Initialize OpenAI (for fallback)
        if TTSConfig.OPENAI_API_KEY:
            try:
                from voice_providers import OpenAIVoiceProvider
                self.openai = OpenAIVoiceProvider()
                logger.info("✅ OpenAI TTS loaded (fallback)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load OpenAI TTS: {e}")
        
        if not self.uplift and not self.openai:
            logger.error("❌ No TTS providers available!")
    
    def _preprocess_urdu_text(self, text: str) -> str:
        """Apply Pakistani vocabulary fixes and Roman->Urdu script transliteration."""
        import os
        try:
            from prompts import enforce_pakistani_roman_urdu, roman_to_urdu_script
            # 1. Apply vocabulary safety net (Hindi -> Pakistani Urdu)
            text = enforce_pakistani_roman_urdu(text)
            
            # 2. Transliterate Roman Urdu -> Urdu script (Arabic characters)
            urdu_script_tts = os.getenv("URDU_SCRIPT_TTS", "true").strip().lower() in ("1", "true", "yes", "on")
            if urdu_script_tts:
                converted = roman_to_urdu_script(text)
                if converted and converted != text:
                    logger.info(f"[TTS Manager] transliterated Roman→Urdu script ({len(converted)} chars)")
                    text = converted
        except Exception as e:
            logger.warning(f"[TTS Manager] Preprocessing failed: {e}")
        return text

    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   output_format: Optional[str] = None,
                   language: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech with automatic provider selection.
        """
        # Resolve and normalize language code
        lang = language or detect_language(text)
        lang = (lang or "").strip().lower()
        if lang in ("roman_urdu", "urdu", "mixed", "ur"):
            lang = "ur"
        elif lang in ("sindhi", "sd"):
            lang = "sd"
        else:
            lang = "en"
            
        logger.info(f"📝 Resolved TTS language: {lang}")
        
        # For Urdu/Sindhi, prefer Uplift
        if lang in ['ur', 'sd']:
            if lang == 'ur':
                text = self._preprocess_urdu_text(text)
                
            if self.uplift:
                logger.info(f"🔊 Using Uplift for {lang} text")
                # Resolve proper voice ID from mapping
                vid = voice_id or get_voice_for_language(lang)
                result = self.uplift.synthesize(text, vid, output_format)
                if result:
                    return result
                logger.warning(f"⚠️ Uplift failed for {lang}, trying fallback")
            
            # Fallback to OpenAI if not forced
            if not TTSConfig.FORCE_UPLIFT_FOR_URDU and (self.openai or TTSConfig.OPENAI_API_KEY):
                logger.info(f"🔊 Falling back to OpenAI for {lang} text")
                return self._synthesize_openai(text)
            
            return None
        
        # For English, use configured provider
        if TTSConfig.TTS_PROVIDER == 'uplift' and self.uplift:
            vid = voice_id or get_voice_for_language(lang)
            result = self.uplift.synthesize(text, vid, output_format)
            if result:
                return result
        
        # Fallback to OpenAI
        return self._synthesize_openai(text)
    
    def _synthesize_openai(self, text: str) -> Optional[bytes]:
        """Synthesize using OpenAI TTS."""
        if not self.openai:
            if TTSConfig.OPENAI_API_KEY:
                try:
                    from voice_providers import OpenAIVoiceProvider
                    self.openai = OpenAIVoiceProvider()
                except Exception as e:
                    logger.error(f"❌ OpenAI fallback initialization failed: {e}")
                    return None
            else:
                logger.error("❌ OpenAI API key not configured for fallback")
                return None
        try:
            result = self.openai.synthesize(text)
            if result:
                logger.info(f"✅ OpenAI TTS generated: {len(result)} bytes")
                return result
        except Exception as e:
            logger.error(f"❌ OpenAI TTS error: {e}")
        return None
    
    def synthesize_and_upload(self, text: str, room_id: str, message_id: str,
                               voice_id: Optional[str] = None,
                               language: Optional[str] = None) -> Optional[str]:
        """
        Synthesize and upload to storage.
        """
        # Resolve and normalize language code
        lang = language or detect_language(text)
        lang = (lang or "").strip().lower()
        if lang in ("roman_urdu", "urdu", "mixed", "ur"):
            lang = "ur"
        elif lang in ("sindhi", "sd"):
            lang = "sd"
        else:
            lang = "en"
            
        logger.info(f"📝 Resolved upload TTS language: {lang}")
        
        # Get appropriate voice
        if not voice_id:
            voice_id = get_voice_for_language(lang)
            
        if lang == 'ur':
            text = self._preprocess_urdu_text(text)
        
        # Try Uplift for Urdu/Sindhi
        if lang in ['ur', 'sd'] and self.uplift:
            result = self.uplift.synthesize_and_upload(text, room_id, message_id, voice_id)
            if result:
                return result
            logger.warning(f"⚠️ Uplift upload failed for {lang}, trying fallback")
        
        # Try English via configured provider (if uplift)
        if lang == 'en' and TTSConfig.TTS_PROVIDER == 'uplift' and self.uplift:
            result = self.uplift.synthesize_and_upload(text, room_id, message_id, voice_id)
            if result:
                return result
        
        # Try OpenAI fallback
        if not (lang in ['ur', 'sd'] and TTSConfig.FORCE_UPLIFT_FOR_URDU):
            audio_data = self._synthesize_openai(text)
            if audio_data:
                from supabase_client import upload_audio_to_storage
                storage_path = f"{room_id}/{message_id}.mp3"
                if upload_audio_to_storage(storage_path, audio_data):
                    logger.info(f"✅ OpenAI audio uploaded to: {storage_path}")
                    return storage_path
        
        return None

# Singleton instance
tts_manager = TTSManager()
