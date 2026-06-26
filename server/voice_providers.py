from __future__ import annotations

# ============================================================
# 🔊 Swappable Text-to-Speech (TTS) provider layer
# ------------------------------------------------------------
# A small abstraction so /tts can switch between vendors via the
# TTS_PROVIDER env var without the Flask route (or the frontend)
# changing. Every provider returns raw MP3 bytes from synthesize().
# ============================================================

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

logger = logging.getLogger("voice-providers")

DEFAULT_TTS_PROVIDER = "openai"

# Smallest plausible speech clip. Real TTS audio (even one word) is multiple KB; an error
# string / HTML page / truncated body is far smaller. Used to reject non-audio bodies that
# some providers return with a 200 status, which would otherwise be served (and cached) as
# broken audio → silent playback.
_MIN_AUDIO_BYTES = 256


def _looks_like_audio(body: bytes) -> bool:
    """Heuristic: does `body` look like a real audio clip (not a text/HTML/JSON error or a
    truncated/empty body)? Accepts known audio container/codec magic numbers, or any
    sufficiently large non-text binary; rejects small or text-leading bodies."""
    if not body or len(body) < _MIN_AUDIO_BYTES:
        return False
    if body[:1] in (b"<", b"{", b"["):                 # HTML / XML / JSON error body
        return False
    if body[:3] == b"ID3":                              # MP3 with ID3 tag
        return True
    if body[0] == 0xFF and (body[1] & 0xE0) == 0xE0:   # MPEG-1/2 audio frame sync (raw MP3)
        return True
    if body[:4] in (b"RIFF", b"OggS", b"fLaC"):        # WAV / OGG(Opus) / FLAC
        return True
    if body[4:8] == b"ftyp":                            # MP4 / M4A / AAC container
        return True
    # No recognized magic, but it's a sizeable non-text binary — accept rather than
    # over-reject (some endpoints stream raw frames whose first byte varies).
    return len(body) >= 512


class VoiceProviderError(Exception):
    """Raised when a provider is misconfigured or synthesis fails."""


class VoiceProvider(ABC):
    """Interface for a text-to-speech backend that yields MP3 bytes."""

    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, language: Optional[str] = None) -> bytes:
        """Return MP3 audio bytes for `text`.

        `language` is an optional hint; providers that select language via a
        fixed voice id may ignore it. Raise VoiceProviderError on failure.
        """
        raise NotImplementedError

    def synthesize_streaming(self, text: str, language: Optional[str] = None):
        """Yield MP3 bytes in chunks for low-latency streaming.

        Default implementation wraps synthesize() so providers that don't
        override this still work — they just buffer everything in one chunk.
        Providers that support true streaming should override this.
        """
        yield self.synthesize(text, language)


# ------------------------------------------------------------
# OpenAI — tts-1 is the real-time optimised model (~3× faster than
# gpt-4o-mini-tts for first-byte latency; use gpt-4o-mini-tts only
# when instruction-following in the prompt matters).
# Override via OPENAI_TTS_MODEL env var if a different model is needed.
# ------------------------------------------------------------
class OpenAIVoiceProvider(VoiceProvider):
    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "alloy",
    ):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key or not key.strip():
            raise VoiceProviderError("OPENAI_API_KEY not configured")
        try:
            from openai import OpenAI
        except ImportError as e:
            raise VoiceProviderError("openai package not installed") from e
        # Bound TTS calls (default SDK is 600 s × 2 retries). A hung synthesis must not
        # pin a server thread and starve concurrent /stt requests. tts-1 normally
        # returns in well under a second, so 15 s / 1 retry is generous.
        self._client = OpenAI(api_key=key, timeout=15.0, max_retries=1)
        self._model = os.getenv("OPENAI_TTS_MODEL", model)
        self._voice = os.getenv("OPENAI_TTS_VOICE", voice)

    def synthesize(self, text: str, language: Optional[str] = None) -> bytes:
        try:
            res = self._client.audio.speech.create(
                model=self._model,
                voice=self._voice,
                input=text,
            )
            return res.read()
        except Exception as e:
            raise VoiceProviderError(f"OpenAI synthesis failed: {e}") from e

    def synthesize_streaming(self, text: str, language: Optional[str] = None):
        """Stream MP3 bytes directly from OpenAI without buffering on the server.

        OpenAI generates audio progressively; this forwards chunks to Flask as
        they arrive, reducing time-to-first-byte from ~synthesis-duration to
        ~200–400 ms.
        """
        try:
            with self._client.audio.speech.with_streaming_response.create(
                model=self._model,
                voice=self._voice,
                input=text,
            ) as response:
                for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk
        except Exception as e:
            raise VoiceProviderError(f"OpenAI streaming synthesis failed: {e}") from e


# ------------------------------------------------------------
# Uplift AI — REST endpoint returning audio bytes
# ------------------------------------------------------------
class UpliftAIVoiceProvider(VoiceProvider):
    name = "uplift"
    ENDPOINT = "https://api.upliftai.org/v1/synthesis/text-to-speech"

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        output_format: str = "MP3_22050_128",
        timeout: float = 8.0,
    ):
        # Accept either env name (.env historically used UPLIFT_API_KEY).
        self._api_key = (
            api_key
            or os.getenv("UPLIFTAI_API_KEY")
            or os.getenv("UPLIFT_API_KEY")
        )
        if not self._api_key or not self._api_key.strip():
            raise VoiceProviderError("UPLIFTAI_API_KEY (or UPLIFT_API_KEY) not configured")
        # A generic voice id is optional now — the actual id is resolved per
        # language in synthesize(), so the provider can init with just the key.
        self._voice_id = voice_id or os.getenv("UPLIFT_VOICE_ID")
        # Resolve Urdu voice ID, ignoring template placeholders
        urdu_voice = os.getenv("UPLIFT_ROMAN_URDU_VOICE_ID")
        if urdu_voice:
            urdu_voice = urdu_voice.strip()
            if not urdu_voice or urdu_voice.lower() in ("pakistani-urdu-voice-id", "your-pakistani-urdu-voice-id", "your-voice-id-here"):
                urdu_voice = None

        self._voice_id_urdu = (
            urdu_voice
            or os.getenv("UPLIFT_VOICE_ID_URDU")
            or self._voice_id
        )
        self._voice_id_en = os.getenv("UPLIFT_VOICE_ID_EN") or self._voice_id
        self._output_format = os.getenv("UPLIFT_OUTPUT_FORMAT", output_format)
        # Fail FAST: a slow/hanging Uplift must not stall the /tts request. After this
        # window we raise → synthesize_for_language() falls back to OpenAI, so a Roman-Urdu
        # moderator reply is still spoken (OpenAI voice) within seconds instead of going
        # silent. Healthy Uplift synthesis is ~1-3s, so 8s is generous. Override via env.
        try:
            self._timeout = float(os.getenv("UPLIFT_TIMEOUT", timeout))
        except (TypeError, ValueError):
            self._timeout = timeout

    def _voice_for_language(self, language: Optional[str]) -> str:
        """Pick the configured voice id for the language, or raise if none is set."""
        if language in ("roman_urdu", "urdu"):
            voice = self._voice_id_urdu
        else:
            voice = self._voice_id_en
        if not voice or not voice.strip():
            raise VoiceProviderError(
                f"No Uplift voice id configured for language={language!r} "
                "(set UPLIFT_ROMAN_URDU_VOICE_ID / UPLIFT_VOICE_ID_EN / UPLIFT_VOICE_ID)"
            )
        return voice

    def synthesize(self, text: str, language: Optional[str] = None) -> bytes:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "voiceId": self._voice_for_language(language),
            "text": text,
            "outputFormat": self._output_format,
        }
        # CRITICAL DIAGNOSTIC: this synchronous POST is the single most likely place for a
        # Roman-Urdu /tts request to stall. If "POST start" logs but "POST done" never does,
        # the Uplift endpoint is the blocking point (until the timeout below fires).
        logger.info(
            f"[TTS] Uplift POST start: lang={language!r} voice={payload['voiceId']!r} "
            f"chars={len(text)} timeout={self._timeout}s"
        )
        _t0 = time.monotonic()
        try:
            resp = requests.post(
                self.ENDPOINT, json=payload, headers=headers, timeout=self._timeout
            )
        except requests.RequestException as e:
            logger.warning(f"[TTS] Uplift POST failed after {time.monotonic() - _t0:.1f}s: {e}")
            raise VoiceProviderError(f"Uplift request failed: {e}") from e
        logger.info(
            f"[TTS] Uplift POST done: status={resp.status_code} "
            f"bytes={len(resp.content or b'')} in {time.monotonic() - _t0:.1f}s"
        )

        if resp.status_code >= 400:
            # Surface the API's own message when available, else the raw body.
            detail = resp.text[:300]
            raise VoiceProviderError(
                f"Uplift synthesis failed (HTTP {resp.status_code}): {detail}"
            )
        return self._extract_audio(resp)

    def _extract_audio(self, resp) -> bytes:
        """Return playable audio bytes from an Uplift 2xx response.

        Uplift may return raw audio OR a JSON envelope (audio URL / base64). We must
        NOT pass JSON through as audio (the browser plays nothing → silent Roman Urdu).
        Anything we can't turn into audio raises VoiceProviderError so /tts falls back
        to OpenAI — guaranteeing the moderator is voiced in BOTH languages.
        """
        ctype = (resp.headers.get("Content-Type") or "").lower()
        body = resp.content or b""
        looks_json = "application/json" in ctype or body[:1] in (b"{", b"[")
        logger.info(f"[TTS] Uplift response: ctype={ctype!r} bytes={len(body)} json={looks_json}")

        if looks_json:
            try:
                data = resp.json()
            except Exception as e:
                raise VoiceProviderError(f"Uplift returned non-audio response: {e}")
            # Common envelope shapes — URL to fetch, or inline base64.
            url = data.get("audioUrl") or data.get("url") or data.get("audio_url")
            if url:
                try:
                    a = requests.get(url, timeout=self._timeout)
                except requests.RequestException as e:
                    raise VoiceProviderError(f"Uplift audio URL fetch failed: {e}") from e
                if a.status_code >= 400 or not a.content:
                    raise VoiceProviderError(f"Uplift audio URL returned HTTP {a.status_code}")
                return self._validated_audio(a.content, "audioUrl")
            b64 = (
                data.get("audioContent") or data.get("audio")
                or data.get("audioBase64") or data.get("data")
            )
            if isinstance(b64, str) and b64.strip():
                import base64
                try:
                    decoded = base64.b64decode(b64)
                except Exception as e:
                    raise VoiceProviderError(f"Uplift base64 decode failed: {e}") from e
                return self._validated_audio(decoded, "base64")
            raise VoiceProviderError(f"Uplift JSON had no audio field (keys={list(data)[:6]})")

        # Raw (non-JSON) body. Validate it really IS audio before returning — a 200 carrying
        # a short text/HTML error or a truncated body must NOT be passed through as audio
        # (it would play nothing and, worse, get cached). On failure we raise so /tts falls
        # back to OpenAI, guaranteeing the moderator is still voiced.
        return self._validated_audio(body, "raw body")

    @staticmethod
    def _validated_audio(body: bytes, where: str) -> bytes:
        if not _looks_like_audio(body):
            raise VoiceProviderError(
                f"Uplift {where} is not playable audio "
                f"({len(body or b'')} bytes, head={(body or b'')[:16]!r})"
            )
        return body


# ------------------------------------------------------------
# Selector
# ------------------------------------------------------------
_PROVIDERS = {
    "openai": OpenAIVoiceProvider,
    "uplift": UpliftAIVoiceProvider,
}


def get_voice_provider(name: Optional[str] = None) -> VoiceProvider:
    """Build the active provider from `name` or the TTS_PROVIDER env var.

    Defaults to "openai". Raises VoiceProviderError for an unknown name or a
    provider that is missing its credentials.
    """
    selected = (name or os.getenv("TTS_PROVIDER") or DEFAULT_TTS_PROVIDER).strip().lower()
    provider_cls = _PROVIDERS.get(selected)
    if provider_cls is None:
        raise VoiceProviderError(
            f"Unknown TTS_PROVIDER {selected!r} (expected one of {sorted(_PROVIDERS)})"
        )
    return provider_cls()
