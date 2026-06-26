#!/usr/bin/env python
"""
Test script for Uplift TTS integration.
Run: python scripts/test_uplift_tts.py
"""

import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 encoding for stdout/stderr to support emojis/special chars on Windows command prompt
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load dotenv if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / 'server' / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded env from: {env_path}")
except ImportError:
    pass

from server.config import TTSConfig
from server.tts.language import detect_language, get_voice_for_language, should_use_uplift
from server.tts.uplift import uplift_tts
from server.tts.tts_manager import tts_manager

def test_config():
    """Test configuration loading."""
    print("\n[CONFIG] TTS Configuration:")
    print(f"  Provider: {TTSConfig.TTS_PROVIDER}")
    print(f"  Uplift API Key: {'[SET] Set' if TTSConfig.UPLIFT_API_KEY else '[MISSING] Missing'}")
    print(f"  Uplift Voice: {TTSConfig.UPLIFT_DEFAULT_VOICE}")
    print(f"  OpenAI API Key: {'[SET] Set' if TTSConfig.OPENAI_API_KEY else '[MISSING] Missing'}")
    print(f"  Force Uplift for Urdu: {TTSConfig.FORCE_UPLIFT_FOR_URDU}")
    return TTSConfig.validate()

def test_language_detection():
    """Test language detection."""
    print("\n[LANG] Language Detection Tests:")
    
    test_cases = [
        ("السلام علیکم! آج کیسے ہیں؟", "ur"),
        ("Hello, how are you today?", "en"),
        ("Mujhe Urdu mein baat karni hai", "ur"),  # Roman Urdu
        ("Aap kaise hain?", "ur"),  # Roman Urdu
        ("I am speaking English", "en"),
        ("کیا آپ کو یہ پسند ہے؟", "ur"),
        ("This has some Urdu: aap kaise ho?", "ur"),
    ]
    
    for text, expected in test_cases:
        detected = detect_language(text)
        voice = get_voice_for_language(detected)
        use_uplift = should_use_uplift(text)
        status = "[PASS]" if detected == expected else "[WARN]"
        print(f"  {status} '{text[:30]}...' -> {detected} (expected: {expected})")
        print(f"     Voice: {voice}, Use Uplift: {use_uplift}")

def test_uplift_synthesis():
    """Test Uplift TTS synthesis."""
    print("\n[SYNTH] Uplift TTS Synthesis Tests:")
    
    test_texts = [
        ("السلام علیکم! آج کیسے ہیں؟", "ur"),
        ("Hello, welcome to the discussion!", "en"),
        ("Mujhe Roman Urdu mein baat karni hai", "ur"),
    ]
    
    for text, lang in test_texts:
        print(f"\n  Testing: {text[:40]}...")
        
        # Get voice for language
        voice = get_voice_for_language(lang)
        print(f"  Voice: {voice}")
        
        # Synthesize
        audio = uplift_tts.synthesize(text, voice_id=voice)
        if audio:
            filename = f"test_{lang}_{hash(text)}.mp3"
            with open(filename, "wb") as f:
                f.write(audio)
            print(f"  [OK] Generated: {filename} ({len(audio)} bytes)")
        else:
            print("  [ERROR] Failed to generate audio")

def test_tts_manager():
    """Test TTS manager with fallback."""
    print("\n[MANAGER] TTS Manager Tests:")
    
    test_texts = [
        ("السلام علیکم! آج کیسے ہیں؟", "ur"),
        ("Hello, how are you?", "en"),
    ]
    
    for text, lang in test_texts:
        print(f"\n  Testing: {text[:40]}...")
        
        # Use TTS manager
        audio = tts_manager.synthesize(text)
        if audio:
            filename = f"test_manager_{lang}_{hash(text)}.mp3"
            with open(filename, "wb") as f:
                f.write(audio)
            print(f"  [OK] Generated: {filename} ({len(audio)} bytes)")
            print(f"  Provider used: {'Uplift' if should_use_uplift(text) else 'OpenAI'}")
        else:
            print("  [ERROR] Failed to generate audio")

def main():
    """Run all tests."""
    print("Uplift TTS Integration Tests")
    print("=" * 50)
    
    # Test config
    if not test_config():
        print("\n[ERROR] Configuration validation failed. Please check environment variables.")
        sys.exit(1)
    
    # Test language detection
    test_language_detection()
    
    # Test Uplift synthesis
    test_uplift_synthesis()
    
    # Test TTS manager
    test_tts_manager()
    
    print("\n[OK] All tests complete!")
    print("[INFO] Check for generated MP3 files in the current directory.")

if __name__ == "__main__":
    main()
