import re
import logging

from config import TTSConfig

logger = logging.getLogger(__name__)

# Urdu character set (Arabic script used for Urdu)
URDU_CHARS = set('آبپتثجچحخدذرزژسشصضطظعغفقکگلمنوہیے')
# Sindhi additional characters
SINDHI_CHARS = set('ڀٻپٽٿڃچڇڊڌڍڏڙڦڪ')

# Distinctive Latin-script Urdu tokens that effectively never occur in English text.
# A single hit is enough to classify a message as Roman Urdu.
ROMAN_URDU_WORDS = frozenset(
    {
        "hai", "hain", "nahi", "nahin", "nai", "kya", "kyun", "kyu", "kyunki",
        "aap", "ap", "mujhe", "mujhay", "tum", "tumhe", "hum", "mera", "meri",
        "tera", "teri", "unka", "kaise", "kaisa", "kahan", "kab", "acha",
        "accha", "achha", "theek", "thik", "bohot", "bahut", "bhai", "yaar",
        "haan", "kuch", "kuchh", "matlab", "samajh", "dekho", "suno", "chalo",
        "raha", "rahe", "rahi", "karna", "karo", "krna", "kro",
        "karein", "karenge", "lekin", "magar", "abhi", "phir", "zyada", "ziada",
        "kam", "paani", "pani", "behtar", "wala", "wali", "kyunke", "mil", "rakho",
        "sahi", "galat", "ghalat", "chahiye", "chahie", "hoga", "hogi", "hota",
        "karte", "karta", "karti", "bana", "banao", "socho", "batao", "samjho",
    }
)

def detect_language(text: str) -> str:
    """
    Detect the language of the text.
    Returns: 'ur' for Urdu (Arabic script or Roman), 'sd' for Sindhi, 'en' for English.
    """
    if not text or not text.strip():
        return 'en'
    
    # Check for Urdu script characters
    urdu_count = sum(1 for c in text if c in URDU_CHARS)
    sindhi_count = sum(1 for c in text if c in SINDHI_CHARS)
    
    # If we have Urdu/Sindhi characters, detect accordingly
    if urdu_count > 0:
        # Check if it's Sindhi (has Sindhi-specific chars)
        if sindhi_count > 0 and sindhi_count > urdu_count * 0.3:
            return 'sd'
        return 'ur'
    
    # Check for Roman Urdu patterns (English script but Urdu words)
    tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    for tok in tokens:
        if tok in ROMAN_URDU_WORDS:
            return 'ur'
    
    # Default to English
    return 'en'

def get_voice_for_language(language: str) -> str:
    """
    Get the appropriate voice ID for a language.
    """
    return TTSConfig.get_voice_for_language(language)

def should_use_uplift(text: str) -> bool:
    """
    Determine if we should use Uplift TTS or fallback to OpenAI.
    Use Uplift for Urdu/Sindhi, OpenAI for English unless forced.
    """
    language = detect_language(text)
    
    # Use Uplift for Urdu/Sindhi (always, unless forced otherwise)
    if language in ['ur', 'sd']:
        return True
    
    # For English, use configured provider
    return TTSConfig.TTS_PROVIDER == 'uplift'
