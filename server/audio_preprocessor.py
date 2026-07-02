"""
server/audio_preprocessor.py
=============================
Lightweight Audio Preprocessor for STT Input.
Provides Noise Reduction & Voice Activity Detection (VAD) to improve transcription accuracy.
Fails open gracefully if external audio packages (e.g. webrtcvad, noisereduce) are absent.
"""

import logging
import math
import struct
from typing import Tuple

logger = logging.getLogger("audio-preprocessor")

# Try importing WebRTC VAD if installed
try:
    import webrtcvad
    _VAD_AVAILABLE = True
except ImportError:
    _VAD_AVAILABLE = False
    logger.info("ℹ️ webrtcvad not installed; using RMS energy VAD fallback.")

# Try importing noisereduce if installed
try:
    import noisereduce as nr
    import numpy as np
    _NOISEREDUCE_AVAILABLE = True
except ImportError:
    _NOISEREDUCE_AVAILABLE = False
    logger.info("ℹ️ noisereduce not installed; skipping spectral noise reduction.")


def calculate_rms_energy(pcm_bytes: bytes) -> float:
    """Calculate Root Mean Square (RMS) energy for 16-bit PCM audio bytes."""
    if not pcm_bytes:
        return 0.0
    count = len(pcm_bytes) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"<{count}h", pcm_bytes[:count*2])
    sum_squares = sum(s * s for s in shorts)
    return math.sqrt(sum_squares / count)


import os

VAD_RMS_THRESHOLD = float(os.getenv("VAD_RMS_THRESHOLD", "100.0"))
VAD_SPEECH_RATIO = float(os.getenv("VAD_SPEECH_RATIO", "0.20"))


def is_speech(audio_bytes: bytes, sample_rate: int = 16000) -> bool:
    """
    Detect if audio contains speech.
    Uses WebRTC VAD if available; falls back to RMS energy thresholding.
    Configurable via VAD_RMS_THRESHOLD and VAD_SPEECH_RATIO environment variables.
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return False

    if _VAD_AVAILABLE:
        try:
            vad = webrtcvad.Vad(2)  # Aggressiveness mode 2 (moderate)
            frame_duration_ms = 30
            frame_bytes = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
            
            speech_frames = 0
            total_frames = 0
            for offset in range(0, len(audio_bytes) - frame_bytes, frame_bytes):
                frame = audio_bytes[offset:offset + frame_bytes]
                if vad.is_speech(frame, sample_rate):
                    speech_frames += 1
                total_frames += 1
                
            if total_frames > 0:
                speech_ratio = speech_frames / total_frames
                return speech_ratio >= VAD_SPEECH_RATIO
        except Exception as ex:
            logger.debug("webrtcvad error, fallback to RMS energy: %s", ex)

    # Fallback: RMS Energy Check
    rms = calculate_rms_energy(audio_bytes)
    return rms >= VAD_RMS_THRESHOLD  # Threshold for audible speech in 16-bit PCM


def denoise_audio(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """
    Apply spectral noise reduction to audio bytes if noisereduce is installed.
    Otherwise returns original audio_bytes.
    """
    if not _NOISEREDUCE_AVAILABLE or not audio_bytes:
        return audio_bytes

    try:
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        reduced_np = nr.reduce_noise(y=audio_np, sr=sample_rate)
        return reduced_np.astype(np.int16).tobytes()
    except Exception as ex:
        logger.warning("Noise reduction failed; returning original audio: %s", ex)
        return audio_bytes


def process_audio_for_stt(audio_bytes: bytes) -> Tuple[bytes, bool]:
    """
    Preprocess audio prior to STT transcription:
    1. Denoise audio.
    2. Check VAD / speech presence.
    Returns (processed_audio_bytes, contains_speech).
    """
    cleaned_bytes = denoise_audio(audio_bytes)
    has_voice = is_speech(cleaned_bytes)
    return cleaned_bytes, has_voice
