from __future__ import annotations

# ============================================================
# 🔊 Swappable Text-to-Speech (TTS) provider layer
# ------------------------------------------------------------
# A small abstraction so /tts can switch between vendors via the
# TTS_PROVIDER env var without the Flask route (or the frontend)
# changing. Every provider returns raw MP3 bytes from synthesize().
# ============================================================

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

logger = logging.getLogger("voice-providers")

DEFAULT_TTS_PROVIDER = "openai"


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


# ------------------------------------------------------------
# OpenAI — wraps the existing gpt-4o-mini-tts call
# ------------------------------------------------------------
class OpenAIVoiceProvider(VoiceProvider):
    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
    ):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key or not key.strip():
            raise VoiceProviderError("OPENAI_API_KEY not configured")
        try:
            from openai import OpenAI
        except ImportError as e:
            raise VoiceProviderError("openai package not installed") from e
        self._client = OpenAI(api_key=key)
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
        timeout: float = 30.0,
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
        self._voice_id_urdu = os.getenv("UPLIFT_VOICE_ID_URDU") or self._voice_id
        self._voice_id_en = os.getenv("UPLIFT_VOICE_ID_EN") or self._voice_id
        self._output_format = os.getenv("UPLIFT_OUTPUT_FORMAT", output_format)
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
                "(set UPLIFT_VOICE_ID_URDU / UPLIFT_VOICE_ID_EN / UPLIFT_VOICE_ID)"
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
        try:
            resp = requests.post(
                self.ENDPOINT, json=payload, headers=headers, timeout=self._timeout
            )
        except requests.RequestException as e:
            raise VoiceProviderError(f"Uplift request failed: {e}") from e

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
                return a.content
            b64 = (
                data.get("audioContent") or data.get("audio")
                or data.get("audioBase64") or data.get("data")
            )
            if isinstance(b64, str) and b64.strip():
                import base64
                try:
                    return base64.b64decode(b64)
                except Exception as e:
                    raise VoiceProviderError(f"Uplift base64 decode failed: {e}") from e
            raise VoiceProviderError(f"Uplift JSON had no audio field (keys={list(data)[:6]})")

        if not body:
            raise VoiceProviderError("Uplift returned empty audio")
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
