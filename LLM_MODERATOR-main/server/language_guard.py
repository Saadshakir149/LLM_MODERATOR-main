from __future__ import annotations

# ============================================================
# 🛡️ language_guard.py — HARD output guard: English / Roman Urdu (Latin) ONLY
# ------------------------------------------------------------
# The product supports exactly two languages: English and Roman Urdu, both written in
# the LATIN alphabet. No other script may ever reach the chat or TTS — not Korean,
# Chinese, Japanese, Arabic/Urdu script, Hebrew, Cyrillic, Devanagari, Thai, etc.
#
# This is a deterministic LAST-LINE enforcement net applied at the final output stages
# (moderator text, TTS input). Romanization of Urdu happens upstream; if any non-Latin
# language script still slips through, it is stripped here and flagged so it is visible
# in logs / failure reports. Latin letters, digits, whitespace, punctuation, and emoji
# are preserved.
#
# ADDITIVE guard — it does not modify the frozen detect_language / normalization logic;
# it enforces the already-stated language policy.
# ============================================================

import re
from typing import Any, Dict, List, Tuple

SUPPORTED_LANGUAGES = ("en", "ur")  # ur == Roman Urdu (Latin script)

# Disallowed language-script Unicode ranges (NOT an allow-list, so emoji/symbols survive).
_DISALLOWED_RANGES = {
    "CJK": "一-鿿㐀-䶿",          # Chinese / Kanji
    "CJK_symbols": "　-〿",
    "Hiragana_Katakana": "぀-ヿ",          # Japanese kana
    "Hangul": "가-힯ᄀ-ᇿ",        # Korean
    "Arabic_Urdu": "؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿",
    "Hebrew": "֐-׿",
    "Cyrillic": "Ѐ-ӿ",
    "Greek": "Ͱ-Ͽ",
    "Devanagari": "ऀ-ॿ",
    "Bengali": "ঀ-৿",
    "Tamil": "஀-௿",
    "Thai": "฀-๿",
    "Fullwidth": "＀-￯",
}

_ALL = "".join(_DISALLOWED_RANGES.values())
_DISALLOWED_RE = re.compile(f"[{_ALL}]")
_PER_SCRIPT_RE = {name: re.compile(f"[{rng}]") for name, rng in _DISALLOWED_RANGES.items()}


def is_supported(text: str) -> bool:
    """True if `text` contains no disallowed (non-Latin language) script."""
    if not text:
        return True
    return _DISALLOWED_RE.search(text) is None


def find_disallowed(text: str) -> List[Dict[str, Any]]:
    """Return [{script, sample}] for each disallowed script present (for logging)."""
    found = []
    if not text:
        return found
    for name, rx in _PER_SCRIPT_RE.items():
        hits = rx.findall(text)
        if hits:
            found.append({"script": name, "count": len(hits), "sample": "".join(hits[:8])})
    return found


def sanitize_to_supported(text: str) -> Tuple[str, bool, List[Dict[str, Any]]]:
    """Strip any disallowed-script characters. Returns (clean, had_disallowed, scripts).

    Latin letters, digits, whitespace, punctuation, and emoji are preserved. Disallowed
    characters are replaced with a space and collapsed, so the result is always
    English/Roman-Urdu-only text (possibly with gaps where foreign script was removed).
    """
    if not text or _DISALLOWED_RE.search(text) is None:
        return text, False, []
    scripts = find_disallowed(text)
    cleaned = _DISALLOWED_RE.sub(" ", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    return cleaned, True, scripts
