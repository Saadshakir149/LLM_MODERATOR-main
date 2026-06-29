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

import re
import json

# Mapping English, Roman Urdu, and digit numerals to integer values
ORDINAL_MAP = {
    "1": 1, "1st": 1, "first": 1, "pehla": 1, "pehli": 1, "one": 1,
    "2": 2, "2nd": 2, "second": 2, "doosra": 2, "dusra": 2, "two": 2,
    "3": 3, "3rd": 3, "third": 3, "teesra": 3, "tisra": 3, "three": 3,
    "4": 4, "4th": 4, "fourth": 4, "chotha": 4, "chautha": 4, "four": 4,
    "5": 5, "5th": 5, "fifth": 5, "panchwa": 5, "panchwan": 5, "five": 5,
    "6": 6, "6th": 6, "sixth": 6, "chata": 6, "chatha": 6, "six": 6,
    "7": 7, "7th": 7, "seventh": 7, "saatwa": 7, "satwan": 7, "seven": 7,
    "8": 8, "8th": 8, "eighth": 8, "aatwa": 8, "athwan": 8, "eight": 8,
    "9": 9, "9th": 9, "ninth": 9, "nawa": 9, "nawan": 9, "nine": 9,
    "10": 10, "10th": 10, "tenth": 10, "daswa": 10, "daswan": 10, "ten": 10,
    "11": 11, "11th": 11, "eleventh": 11, "gyarwah": 11, "gyarwan": 11, "eleven": 11,
    "12": 12, "12th": 12, "twelfth": 12, "barwah": 12, "barwan": 12, "twelve": 12
}

def parse_ranking_proposals_local(message: str, canonical_items: List[str]) -> List[tuple[int, str]]:
    """Local parser using regex and canonical item matching."""
    from data_retriever import normalize_item_name
    proposals = []
    
    # Split message into clauses by common separators
    clauses = re.split(r"[,.;!?]|\band\b|\btoh\b|\baur\b", message.lower())
    
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        
        # Find if any ordinal or digit is in the clause
        tokens = re.findall(r"\b\w+(?:st|nd|rd|th)?\b", clause)
        clause_ranks = []
        for tok in tokens:
            if tok in ORDINAL_MAP:
                clause_ranks.append(ORDINAL_MAP[tok])
        
        # If no ranks found, check for standalone digits 1-12
        if not clause_ranks:
            digits = re.findall(r"\b([1-9]|1[0-2])\b", clause)
            for d in digits:
                clause_ranks.append(int(d))
                
        if not clause_ranks:
            continue
            
        # Try to normalize item name in this clause
        item = normalize_item_name(clause, canonical_items)
        if item:
            for rank in clause_ranks:
                proposals.append((rank, item))
                
    return proposals

def llm_parse_ranking_proposals(message_text: str, canonical_items: List[str]) -> List[tuple[int, str]]:
    """LLM fallback parser to extract item rankings from free text when regex fails."""
    try:
        from prompts import call_llm
    except ImportError:
        return []
        
    items_list_str = "\n".join(f"- {item}" for item in canonical_items)
    
    system_prompt = f"""You are a precise Desert Survival ranking parser.
Your task is to extract proposed rankings of items from a participant's message.

Canonical list of items:
{items_list_str}

Rules:
1. Extract any proposed item and the rank number (1 to 12) it should occupy.
2. Map the mentioned item to the EXACT matching canonical item from the list above. If it doesn't match any, ignore it.
3. Map ranking words (first, 1st, pehla, second, last, 12th, etc.) to their integer values (1 to 12).
4. Output ONLY valid JSON in this exact format:
{{
  "proposals": [
     {{"rank": 1, "item": "canonical item name"}},
     {{"rank": 12, "item": "canonical item name"}}
  ]
}}
Do NOT output markdown (do not wrap in ```json), thoughts, or extra characters. Just raw JSON."""

    try:
        res = call_llm([message_text], system_prompt=system_prompt, temperature=0.0, max_tokens=150)
        if not res:
            return []
        
        content = res.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        data = json.loads(content)
        proposals = []
        for prop in data.get("proposals", []):
            rank = int(prop.get("rank", 0))
            item = prop.get("item")
            if 1 <= rank <= 12 and item in canonical_items:
                proposals.append((rank, item))
        return proposals
    except Exception as e:
        logger.error(f"LLM parser fallback error: {e}")
        return []

def recompute_ranking_state(room_id: str, students: List[str]):
    """Recompute the consensus status for all 12 items based on participant preferences."""
    st = get_room_state(room_id)
    prefs = st.setdefault("participant_preferences", {})
    st["ranking_state"] = {}
    st["disagreements"] = {}
    
    # Ensure all active students have a preference dict
    for s in students:
        prefs.setdefault(s, {})
        
    try:
        from data_retriever import get_pinned_or_resolve_task_data, get_task_items
        td = get_pinned_or_resolve_task_data(room_id)
        canonical_items = list(td.get("items", []))
    except Exception:
        canonical_items = []
        
    for r in range(1, 13):
        r_str = str(r)
        # Gather votes
        votes = {} # item -> list of students
        for s in students:
            pref_item = prefs[s].get(r_str)
            if pref_item and (not canonical_items or pref_item in canonical_items):
                votes.setdefault(pref_item, []).append(s)
                
        if not votes:
            st["ranking_state"][r_str] = {
                "leading": None,
                "supporters": [],
                "opponents": [],
                "confidence": 0.0,
                "status": "UNSEEN"
            }
            continue
            
        # Sort items by vote count descending
        sorted_votes = sorted(votes.items(), key=lambda kv: len(kv[1]), reverse=True)
        leading_item, supporters = sorted_votes[0]
        
        opponents = []
        for other_item, other_supporters in sorted_votes[1:]:
            opponents.extend(other_supporters)
            
        confidence = round(len(supporters) / len(students), 2) if students else 0.0
        
        # Decide status
        if len(supporters) == len(students):
            status = "AGREED"
            if st.get("discussion_stage") == "consensus":
                status = "FINALIZED"
        elif len(votes) > 1:
            status = "DISPUTED"
            # Add to disagreements map for backward compatibility and active loops
            st["disagreements"][r_str] = list(votes.keys())
        elif len(supporters) >= 2:
            status = "LEADING"
        else:
            status = "MENTIONED"
            
        st["ranking_state"][r_str] = {
            "leading": leading_item,
            "supporters": supporters,
            "opponents": opponents,
            "confidence": confidence,
            "status": status
        }

def format_progress_summary(room_id: str) -> str:
    """Format a detailed progress summary for LLM context injection."""
    st = get_room_state(room_id)
    ranking_state = st.get("ranking_state", {})
    
    try:
        from data_retriever import get_pinned_or_resolve_task_data
        td = get_pinned_or_resolve_task_data(room_id)
        all_items = list(td.get("items", []))
    except Exception:
        all_items = []
        
    agreed_lines = []
    leading_lines = []
    disputed_lines = []
    remaining_items = set(all_items)
    
    for r in range(1, 13):
        r_str = str(r)
        r_state = ranking_state.get(r_str, {})
        status = r_state.get("status", "UNSEEN")
        leading = r_state.get("leading")
        
        if status in ("AGREED", "FINALIZED") and leading:
            supporters = r_state.get("supporters", [])
            agreed_lines.append(f"✅ Rank {r}: {leading} (Agreement: {len(supporters)}/3)")
            if leading in remaining_items:
                remaining_items.remove(leading)
        elif status == "LEADING" and leading:
            supporters = r_state.get("supporters", [])
            leading_lines.append(f"🟡 Rank {r}: {leading} (Agreement: {len(supporters)}/3)")
            if leading in remaining_items:
                remaining_items.remove(leading)
        elif status == "DISPUTED":
            votes = {}
            prefs = st.get("participant_preferences", {})
            for s, s_prefs in prefs.items():
                item = s_prefs.get(r_str)
                if item:
                    votes[item] = votes.get(item, 0) + 1
            items_str = " vs ".join(votes.keys())
            disputed_lines.append(f"🔴 Rank {r}: {items_str}")
            for item in votes.keys():
                if item in remaining_items:
                    remaining_items.remove(item)
                    
    remaining_names = [item.split(" (")[0] for item in remaining_items]
    
    lines = ["Current Progress:"]
    if agreed_lines:
        lines.extend(agreed_lines)
    if leading_lines:
        lines.extend(leading_lines)
    if disputed_lines:
        lines.extend(disputed_lines)
        
    remaining_str = ", ".join(remaining_names) if remaining_names else "None"
    lines.append(f"⚪ Remaining: {remaining_str}")
    
    return "\n".join(lines)

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
        "ranking_state": {str(i): {
            "leading": None,
            "supporters": [],
            "opponents": [],
            "confidence": 0.0,
            "status": "UNSEEN"
        } for i in range(1, 13)},
        "participant_preferences": {},
        "ranking_history": {},
        "parsed_proposals_cache": {},
        "disagreements": {}
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

    # Rebuild ranking memory and preferences from message history
    try:
        from data_retriever import get_pinned_or_resolve_task_data
        td = get_pinned_or_resolve_task_data(room_id)
        canonical_items = list(td.get("items", []))
    except Exception:
        canonical_items = []
        
    cache = st.setdefault("parsed_proposals_cache", {})
    prefs = st.setdefault("participant_preferences", {})
    
    # Initialize preference map for all active students
    for s in students:
        prefs.setdefault(s, {})
        
    for m in messages:
        u = m.get("username") or m.get("sender")
        if u not in students:
            continue
        msg_text = m.get("message") or ""
        msg_id = m.get("id") or m.get("message_id") or f"{u}_{m.get('created_at') or ''}_{hash(msg_text)}"
        
        # Check cache
        if msg_id in cache:
            proposals = cache[msg_id]
        else:
            proposals = parse_ranking_proposals_local(msg_text, canonical_items)
            if not proposals:
                proposals = llm_parse_ranking_proposals(msg_text, canonical_items)
            cache[msg_id] = proposals
            
        # Apply proposals to student preferences and log history
        for rank, item in proposals:
            rank_str = str(rank)
            old_item = prefs[u].get(rank_str)
            if old_item != item:
                prefs[u][rank_str] = item
                
                # Log change to history
                hist = st.setdefault("ranking_history", {}).setdefault(rank_str, [])
                hist.append({
                    "timestamp": m.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "user": u,
                    "item": item
                })
                
    # Recompute consensus metrics
    recompute_ranking_state(room_id, students)

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
    """A compact summary the moderator prompt can consume."""
    st = _room_states.get(room_id)
    if not st:
        return ""
    lang = st["primary_language"]
    lang_directive = (
        "RESPOND ONLY IN ROMAN URDU (Latin script, never Urdu/Arabic script)"
        if lang in ("roman_urdu", "mixed")
        else "RESPOND ONLY IN ENGLISH"
    )
    base_brief = (
        f"LANGUAGE: {lang_directive}; do NOT switch languages between turns. "
        "ROOM STATE — "
        f"language: {lang} (conf {st['language_confidence']}); "
        f"stage: {st['discussion_stage']}; "
        f"dominant: {st['dominant_speaker'] or '—'}; "
        f"quietest: {st['silent_speaker'] or '—'}; "
        f"consensus: {st['consensus_score']}; conflict: {st['conflict_score']}; "
        f"interventions so far: {st['intervention_count']}."
    )
    progress_summary = format_progress_summary(room_id)
    return base_brief + "\n\n" + progress_summary


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

def get_latest_disagreement(room_id: str) -> tuple[str, List[str]]:
    """Return the rank and list of items for the latest active disagreement."""
    st = get_room_state(room_id)
    disagreements = st.get("disagreements", {})
    if not disagreements:
        return "", []
    # return the last one (highest or most recent)
    r = list(disagreements.keys())[-1]
    return r, disagreements[r]
