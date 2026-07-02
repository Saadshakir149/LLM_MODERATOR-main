"""
server/stt_validator.py
======================
STT Validation & Self-Healing Transcribe Layer.
Evaluates transcription quality against domain keywords (desert items, ranking commands)
and detects gibberish / low-confidence transcription output.
"""

import logging
import re
from typing import Tuple, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger("stt-validator")

# Domain Keywords for Desert Survival Task
DESERT_DOMAIN_KEYWORDS = [
    "map", "compass", "water", "knife", "coat", "mirror", "matches", "sheet",
    "flashlight", "book", "salt", "vodka", "canvas", "ranking", "rank", "list",
    "pehla", "doosra", "teesra", "chautha", "panchwan", "cheta", "saatwan", "aathwan",
    "nawan", "daswan", "gyarwan", "barwan", "complete", "pehle", "baar", "karna", "baat"
]

def validate_transcription(text: str, domain_keywords: Optional[List[str]] = None) -> Tuple[bool, float]:
    """
    Validate transcription quality and phonetic similarity against domain words.
    Returns (is_valid, confidence_score).
    """
    if not text or not text.strip():
        return False, 0.0

    words = text.strip().split()
    if len(words) < 1:
        return False, 0.0

    keywords = domain_keywords if domain_keywords else DESERT_DOMAIN_KEYWORDS
    text_lower = text.lower()

    # Calculate max fuzzy ratio against domain vocabulary
    max_similarity = 0.0
    for word in words:
        w_clean = re.sub(r"[^\w]", "", word.lower())
        if not w_clean:
            continue
        for kw in keywords:
            ratio = SequenceMatcher(None, w_clean, kw.lower()).ratio()
            if ratio > max_similarity:
                max_similarity = ratio

    # Check for gibberish indicators (excessive unvoweled consonants or non-words)
    consonant_streak = max((len(match) for match in re.findall(r"[bcdfghjklmnpqrstvwxyz]{5,}", text_lower)), default=0)
    if consonant_streak >= 5 and max_similarity < 0.60:
        logger.warning("Gibberish detected in STT text: '%s'", text)
        return False, round(max_similarity, 2)

    is_valid = max_similarity >= 0.40 or len(words) >= 3
    return is_valid, round(max_similarity, 2)
