import logging
from typing import Optional

from server.config import TTSConfig
from server.tts.language import detect_language, get_voice_for_language, should_use_uplift

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
                from server.tts.uplift import uplift_tts
                self.uplift = uplift_tts
                logger.info("✅ Uplift TTS loaded")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load Uplift TTS: {e}")
        
        # Initialize OpenAI (for fallback)
        if TTSConfig.OPENAI_API_KEY:
            try:
                from server.voice_providers import OpenAIVoiceProvider
                self.openai = OpenAIVoiceProvider()
                logger.info("✅ OpenAI TTS loaded (fallback)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load OpenAI TTS: {e}")
        
        if not self.uplift and not self.openai:
            logger.error("❌ No TTS providers available!")
    
    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   output_format: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech with automatic provider selection.
        """
        language = detect_language(text)
        logger.info(f"📝 Detected language: {language}")
        
        # For Urdu/Sindhi, prefer Uplift
        if language in ['ur', 'sd']:
            if self.uplift:
                logger.info(f"🔊 Using Uplift for {language} text")
                # Resolve proper voice ID from mapping
                vid = voice_id or get_voice_for_language(language)
                result = self.uplift.synthesize(text, vid, output_format)
                if result:
                    return result
                logger.warning(f"⚠️ Uplift failed for {language}, trying fallback")
            
            # Fallback to OpenAI if not forced
            if not TTSConfig.FORCE_UPLIFT_FOR_URDU and (self.openai or TTSConfig.OPENAI_API_KEY):
                logger.info(f"🔊 Falling back to OpenAI for {language} text")
                return self._synthesize_openai(text)
            
            return None
        
        # For English, use configured provider
        if TTSConfig.TTS_PROVIDER == 'uplift' and self.uplift:
            vid = voice_id or get_voice_for_language(language)
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
                    from server.voice_providers import OpenAIVoiceProvider
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
                               voice_id: Optional[str] = None) -> Optional[str]:
        """
        Synthesize and upload to storage.
        """
        language = detect_language(text)
        
        # Get appropriate voice
        if not voice_id:
            voice_id = get_voice_for_language(language)
        
        # Try Uplift for Urdu/Sindhi
        if language in ['ur', 'sd'] and self.uplift:
            result = self.uplift.synthesize_and_upload(text, room_id, message_id, voice_id)
            if result:
                return result
            logger.warning(f"⚠️ Uplift upload failed for {language}, trying fallback")
        
        # Try English via configured provider (if uplift)
        if language == 'en' and TTSConfig.TTS_PROVIDER == 'uplift' and self.uplift:
            result = self.uplift.synthesize_and_upload(text, room_id, message_id, voice_id)
            if result:
                return result
        
        # Try OpenAI fallback
        if not (language in ['ur', 'sd'] and TTSConfig.FORCE_UPLIFT_FOR_URDU):
            audio_data = self._synthesize_openai(text)
            if audio_data:
                from server.supabase_client import upload_audio_to_storage
                storage_path = f"{room_id}/{message_id}.mp3"
                if upload_audio_to_storage(storage_path, audio_data):
                    logger.info(f"✅ OpenAI audio uploaded to: {storage_path}")
                    return storage_path
        
        return None

# Singleton instance
tts_manager = TTSManager()
