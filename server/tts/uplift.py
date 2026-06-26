import os
import requests
import logging
from typing import Optional

from config import TTSConfig

logger = logging.getLogger(__name__)

class UpliftTTS:
    """Uplift AI TTS provider."""
    
    def __init__(self):
        self.api_key = TTSConfig.UPLIFT_API_KEY
        self.base_url = TTSConfig.UPLIFT_TTS_URL
        self.default_voice = TTSConfig.UPLIFT_DEFAULT_VOICE
        self.default_format = TTSConfig.UPLIFT_OUTPUT_FORMAT
        self.max_text_length = TTSConfig.UPLIFT_MAX_TEXT_LENGTH
        
        if not self.api_key:
            logger.warning("⚠️ UPLIFT_API_KEY not set, TTS will fail")
        else:
            logger.info("✅ Uplift TTS initialized")
    
    def synthesize(self, text: str, voice_id: Optional[str] = None, 
                   output_format: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech from text using Uplift API.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID to use (default: from config)
            output_format: Audio format (default: from config)
            
        Returns:
            Audio data as bytes or None if failed
        """
        if not self.api_key:
            logger.error("❌ UPLIFT_API_KEY not configured")
            return None
        
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided for TTS")
            return None
        
        # Trim text if too long
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
            logger.info(f"✂️ Text trimmed to {self.max_text_length} chars")
        
        voice_id = voice_id or self.default_voice
        output_format = output_format or self.default_format
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "voiceId": voice_id,
            "text": text,
            "outputFormat": output_format
        }
        
        try:
            logger.info(f"🔊 Generating Uplift TTS: {text[:50]}...")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check for error status
            if response.status_code != 200:
                logger.error(f"❌ Uplift TTS error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            audio_data = response.content
            logger.info(f"✅ Uplift TTS generated: {len(audio_data)} bytes")
            return audio_data
            
        except requests.exceptions.Timeout:
            logger.error("❌ Uplift TTS request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Uplift TTS API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected Uplift TTS error: {e}")
            return None
    
    def synthesize_and_upload(self, text: str, room_id: str, message_id: str, 
                              voice_id: Optional[str] = None) -> Optional[str]:
        """
        Synthesize speech and upload to Supabase storage.
        
        Args:
            text: Text to synthesize
            room_id: Room ID
            message_id: Message ID
            voice_id: Voice ID (optional)
            
        Returns:
            Storage path if successful, None otherwise
        """
        audio_data = self.synthesize(text, voice_id)
        if not audio_data:
            return None
        
        # Upload to Supabase
        storage_path = f"{room_id}/{message_id}.mp3"
        
        try:
            from supabase_client import upload_audio_to_storage
            success = upload_audio_to_storage(storage_path, audio_data)
            if success:
                logger.info(f"✅ Audio uploaded to: {storage_path}")
                return storage_path
            else:
                logger.error(f"❌ Failed to upload audio to storage")
                return None
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return None

# Singleton instance
uplift_tts = UpliftTTS()
