from __future__ import annotations

# ============================================================
# 🧠 Moderator Room-State Engine (Priority 1)
# ------------------------------------------------------------
# A persistent, per-room state object the moderator reads BEFORE generating each
# response — so decisions rest on accumulated discussion state, not just the last
# few chat lines. Held in memory (process-local; fine for the single-worker setup)
# with optional best-effort snapshots to Supabase.
#
# Fields (per the research spec):
#   primary_language, language_confidence, dominant_speaker, silent_speaker,
#   discussion_stage, consensus_score, conflict_score, intervention_count,
#   last_intervention_time
# Plus bookkeeping: room_id, message_count, updated_at.
# ============================================================

import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("room-state")

# room_id -> state dict
_room_states: Dict[str, Dict[str, Any]] = {}

# Lightweight lexical cues for consensus/conflict scoring (English + Roman Urdu).
# These are heuristics for live moderation signals — NOT validated research measures
# (the rigorous metrics come from the Priority 6 pipeline). Tune with pilot data.
_AGREEMENT_MARKERS = frozenset({
    "agree", "agreed", "yes", "yeah", "ok", "okay", "sure", "sounds good", "consensus",
    "final", "done", "settled", "haan", "haa", "sahi", "theek", "thik", "bilkul",
    "mutfiq", "manzoor", "done hai", "agree hai",
})
_CONFLICT_MARKERS = frozenset({
    "no", "nope", "disagree", "but", "however", "wrong", "not sure", "doubt",
    "nahi", "nahin", "galat", "ghalat", "lekin", "magar", "mushkil", "ikhtilaf",
    "i don't", "i dont", "mujhe nahi", "mujhay nahi",
})

VALID_STAGES = ("warmup", "discussing", "converging", "consensus")


def _default_state(room_id: str) -> Dict[str, Any]:
    return {
        "room_id": room_id,
        "primary_language": "en",
        "language_confidence": 0.0,
        "dominant_speaker": None,
        "silent_speaker": None,
        "discussion_stage": "warmup",
        "consensus_score": 0.0,
        "conflict_score": 0.0,
        "intervention_count": 0,
        "last_intervention_time": 0.0,
        "message_count": 0,
        "updated_at": None,
    }


def get_room_state(room_id: str) -> Dict[str, Any]:
    """Return the room's state, creating a default if it doesn't exist yet."""
    return _room_states.setdefault(room_id, _default_state(room_id))


# Explicit per-room language pin (set from the join-screen selector). When set, it is
# AUTHORITATIVE: the moderator and TTS use it from the very first turn instead of
# inferring from messages — so "Hello" in English still gets a Roman-Urdu reply if the
# group chose Roman Urdu.
_pinned_language: Dict[str, str] = {}


def set_room_language(room_id: str, language: str) -> None:
    """Pin a room's language (join-time choice). 'mixed' is accepted but stored as-is."""
    if room_id and language in ("en", "roman_urdu", "mixed"):
        _pinned_language[room_id] = language
        get_room_state(room_id)["primary_language"] = language


def get_pinned_language(room_id: str) -> Optional[str]:
    """Return the explicit join-time language pin for a room, or None."""
    return _pinned_language.get(room_id)


def reset_room_state(room_id: str) -> None:
    """Drop a room's state (e.g. on session end)."""
    _room_states.pop(room_id, None)
    _pinned_language.pop(room_id, None)


def record_intervention(room_id: str, when: Optional[float] = None) -> Dict[str, Any]:
    """Mark that the moderator just intervened (updates count + timestamp)."""
    st = get_room_state(room_id)
    st["intervention_count"] += 1
    st["last_intervention_time"] = when if when is not None else time.time()
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    return st


def _speaker_counts(messages: List[Dict[str, Any]], students: List[str]) -> Dict[str, int]:
    counts = {s: 0 for s in students}
    for m in messages:
        u = m.get("username") or m.get("sender")
        if u in counts:
            counts[u] += 1
    return counts


def update_room_state(
    room_id: str,
    *,
    messages: List[Dict[str, Any]],
    participants: List[str],
    primary_language: Optional[str] = None,
    language_confidence: Optional[float] = None,
    time_elapsed_min: float = 0.0,
) -> Dict[str, Any]:
    """Recompute derived room state from recent messages + participants.

    Cheap and side-effect-free apart from updating the in-memory store. Called after
    each message and/or on the moderator's polling tick.
    """
    st = get_room_state(room_id)
    students = [p for p in participants if p not in ("Moderator", "System", None, "")]

    counts = _speaker_counts(messages, students)
    total = sum(counts.values())

    # Dominant / silent speaker — only meaningful when there's a real disparity.
    if total > 0 and counts:
        ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        top_name, top_n = ordered[0]
        low_name, low_n = ordered[-1]
        avg = total / len(counts)
        st["dominant_speaker"] = top_name if top_n > avg and top_n > low_n else None
        st["silent_speaker"] = low_name if low_n < avg and low_n < top_n else None

    if primary_language:
        st["primary_language"] = primary_language
    if language_confidence is not None:
        st["language_confidence"] = round(float(language_confidence), 2)

    # Consensus / conflict from the recent STUDENT text window (lexical heuristic).
    recent_student_text = " ".join(
        (m.get("message") or "").lower()
        for m in messages[-12:]
        if (m.get("username") or m.get("sender")) in counts
    )
    agree_hits = sum(1 for w in _AGREEMENT_MARKERS if w in recent_student_text)
    conflict_hits = sum(1 for w in _CONFLICT_MARKERS if w in recent_student_text)
    st["consensus_score"] = round(min(1.0, agree_hits / 6.0), 2)
    st["conflict_score"] = round(min(1.0, conflict_hits / 6.0), 2)

    # Discussion stage from time + consensus signal.
    if total < 3 or time_elapsed_min < 2:
        stage = "warmup"
    elif st["consensus_score"] >= 0.7:
        stage = "consensus"
    elif time_elapsed_min >= 12:
        stage = "converging"
    else:
        stage = "discussing"
    st["discussion_stage"] = stage

    st["message_count"] = total
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    return st


def room_state_brief(room_id: str) -> str:
    """A compact one-line summary the moderator prompt can consume."""
    st = _room_states.get(room_id)
    if not st:
        return ""
    lang = st["primary_language"]
    lang_directive = (
        "RESPOND ONLY IN ROMAN URDU (Latin script, never Urdu/Arabic script)"
        if lang in ("roman_urdu", "mixed")
        else "RESPOND ONLY IN ENGLISH"
    )
    return (
        f"LANGUAGE: {lang_directive}; do NOT switch languages between turns. "
        "ROOM STATE — "
        f"language: {lang} (conf {st['language_confidence']}); "
        f"stage: {st['discussion_stage']}; "
        f"dominant: {st['dominant_speaker'] or '—'}; "
        f"quietest: {st['silent_speaker'] or '—'}; "
        f"consensus: {st['consensus_score']}; conflict: {st['conflict_score']}; "
        f"interventions so far: {st['intervention_count']}."
    )


def snapshot_to_supabase(room_id: str, supabase: Any) -> bool:
    """Best-effort persist of the current state to a room_state_snapshots table.

    Returns False (without raising) if the table doesn't exist yet — so this is safe
    to call before the optional migration is applied.
    """
    st = _room_states.get(room_id)
    if not st or supabase is None:
        return False
    try:
        supabase.table("room_state_snapshots").insert({
            "room_id": room_id,
            "state": st,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception as e:
        logger.debug(f"room_state snapshot skipped for {room_id}: {e}")
        return False
