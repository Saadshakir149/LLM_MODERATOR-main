from __future__ import annotations

# ============================================================
# 🎚️ Conversation recording assembly (ADMIN export only)
# ------------------------------------------------------------
# Concatenates a room's audio clips (participant WebM/Opus + moderator MP3) into
# ONE file in chronological order. Mixed codecs require decoding, so each clip is
# normalized to PCM with a pip-bundled static ffmpeg (imageio-ffmpeg) — no system
# ffmpeg install and no pydub. The realtime /stt + chat paths are untouched; this
# is exercised only by the recording-export endpoint.
# ============================================================

import logging
import subprocess
import wave
from io import BytesIO
from typing import Any, Dict, List

logger = logging.getLogger("audio-export")

try:
    import imageio_ffmpeg  # type: ignore

    _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    _ASSEMBLY_OK = True
except Exception as e:  # pragma: no cover - optional dep
    _FFMPEG_EXE = None
    _ASSEMBLY_OK = False
    logger.warning("Audio assembly unavailable (install imageio-ffmpeg to enable): %s", e)

# Common PCM target so decoded clips concatenate frame-for-frame.
_TARGET_RATE = 44100
_TARGET_CHANNELS = 2
_TARGET_SAMPWIDTH = 2  # 16-bit


class AudioAssemblyError(Exception):
    """Raised when clips cannot be assembled into a single file."""


def assembly_available() -> bool:
    """True when a usable ffmpeg binary (imageio-ffmpeg) is present."""
    return _ASSEMBLY_OK


def _run_ffmpeg(args: List[str], data: bytes) -> bytes:
    proc = subprocess.run(
        [_FFMPEG_EXE, "-hide_banner", "-loglevel", "error", *args],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise AudioAssemblyError(
            (proc.stderr.decode("utf-8", "replace")[:300]) or "ffmpeg failed"
        )
    return proc.stdout


def _decode_to_pcm(data: bytes) -> bytes:
    """Decode any input (auto-detected) to headerless PCM-s16le at the target rate.

    Raw PCM (no WAV header) concatenates byte-for-byte with no chunk-size pitfalls.
    """
    return _run_ffmpeg(
        [
            "-i", "pipe:0",
            "-ac", str(_TARGET_CHANNELS),
            "-ar", str(_TARGET_RATE),
            "-f", "s16le", "pipe:1",
        ],
        data,
    )


def concat_clips(clips: List[Dict[str, Any]], out_format: str = "mp3") -> bytes:
    """Concatenate clips (already in the desired order) into one out_format file.

    Each clip is {"data": bytes, "mime": str, "path": str}. Clips that fail to
    decode are skipped (logged). Raises AudioAssemblyError if assembly is
    unavailable or nothing decodable remains.
    """
    if not _ASSEMBLY_OK:
        raise AudioAssemblyError("ffmpeg (imageio-ffmpeg) not installed")
    if out_format not in ("mp3", "wav"):
        out_format = "mp3"

    pcm = bytearray()
    used = 0
    for c in clips:
        data = c.get("data")
        if not data:
            continue
        try:
            pcm += _decode_to_pcm(data)
            used += 1
        except Exception as e:
            logger.warning("Skipped unreadable clip %s: %s", c.get("path"), e)

    if used == 0:
        raise AudioAssemblyError("No decodable audio clips for this room")

    pcm = bytes(pcm)

    if out_format == "wav":
        # Wrap PCM in a single WAV container (header sizes written correctly by stdlib).
        wav_buf = BytesIO()
        with wave.open(wav_buf, "wb") as w:
            w.setnchannels(_TARGET_CHANNELS)
            w.setsampwidth(_TARGET_SAMPWIDTH)
            w.setframerate(_TARGET_RATE)
            w.writeframes(pcm)
        logger.info("🎚️ Assembled %d clip(s) into one wav", used)
        return wav_buf.getvalue()

    # Encode the concatenated PCM straight to MP3.
    mp3_bytes = _run_ffmpeg(
        [
            "-f", "s16le",
            "-ar", str(_TARGET_RATE),
            "-ac", str(_TARGET_CHANNELS),
            "-i", "pipe:0",
            "-f", "mp3", "pipe:1",
        ],
        pcm,
    )
    logger.info("🎚️ Assembled %d clip(s) into one mp3", used)
    return mp3_bytes
