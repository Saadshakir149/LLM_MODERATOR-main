"""
server/transcription_validator.py
==================================
Validates transcription quality for Roman Urdu and English STT outputs.
Determines whether a transcript is coherent and meaningful or low-confidence gibberish.
"""

import logging
import re
from typing import Tuple, Dict, Any

logger = logging.getLogger("transcription-validator")

FILLER_WORDS = {
    "um", "uh", "ah", "aah", "hmm", "hm", "shh", "shhh", "er", "oh",
    "haan", "hmmm", "mmm", "ooh", "eheh", "urgh"
}

REPETITION_REGEX = re.compile(r"(\b\w+\b)(?:\s+\1){3,}", re.IGNORECASE)
CHAR_REPETITION_REGEX = re.compile(r"(.)\1{4,}", re.IGNORECASE)


def is_valid_transcript(text: str) -> Tuple[bool, str]:
    """
    Validates a transcribed text string.
    Returns (is_valid, reason).

    Criteria:
    - Minimum length of 3 characters.
    - At least 2 words.
    - Not composed entirely of filler words or acoustic noise tokens.
    - No excessive character or word repetitions (model hallucination).
    """
    if not text:
        return False, "empty_text"

    clean = text.strip().lower()
    if len(clean) < 3:
        return False, "too_short"

    words = [w for w in re.split(r"\s+", clean) if w]
    if len(words) < 2:
        return False, "insufficient_words"

    # Check filler words
    meaningful_words = [w for w in words if w not in FILLER_WORDS]
    if not meaningful_words:
        return False, "only_filler_words"

    # Check repetition / model hallucination
    if REPETITION_REGEX.search(clean):
        return False, "excessive_word_repetition"

    if CHAR_REPETITION_REGEX.search(clean):
        return False, "excessive_char_repetition"

    return True, "valid"


def calculate_transcript_confidence(raw_text: str, result_dict: Dict[str, Any]) -> float:
    """
    Computes a normalized confidence score (0.0 to 1.0) combining:
    1. Classifier confidence score from language_guard/classify_and_normalize.
    2. Transcription validation integrity check.
    """
    base_confidence = float(result_dict.get("confidence", 0.85))
    valid, reason = is_valid_transcript(raw_text)

    if not valid:
        logger.info(f"🔍 Transcript validation flagged '{reason}': {raw_text!r}")
        return min(base_confidence, 0.45)

    return base_confidence
