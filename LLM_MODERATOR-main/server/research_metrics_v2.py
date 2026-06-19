from __future__ import annotations

# ============================================================
# 📐 research_metrics_v2.py — AUTHORITATIVE research instrumentation (Priority 6)
# ------------------------------------------------------------
# These are the reproducible measures used for statistical analysis (CHI 2027).
# They are computed deterministically from DURABLE data only:
#   * messages       — username, message, message_type, created_at (ISO), metadata
#   * interventions  — moderator_interventions rows (intervention_type, timestamp)
#   * durations      — {message_id: duration_ms} from voice_recordings (speaking time)
#
# IMPORTANT: this module does NOT read room_state. room_state holds OPERATIONAL
# moderator heuristics; the numbers here are the authoritative research metrics.
#
# Every function is pure and defensively handles the edge cases the study will hit:
# empty rooms, a single participant, missing audio durations, very short sessions,
# and mixed-language sessions (language never affects these counts/timings).
# ============================================================

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from research_metrics import calculate_gini_coefficient, calculate_entropy

logger = logging.getLogger("research_metrics_v2")

_SKIP = {"Moderator", "System", None, ""}

# An "interruption" proxy: a switch to a different speaker within this many seconds
# of the previous student message (overlapping speech can't be captured directly with
# push-to-talk, so this is a documented rapid-turn-switch estimate).
INTERRUPTION_GAP_SEC = 1.5

# Lexical agreement cues for the consensus-progress PROXY (documented, reproducible).
_AGREEMENT_CUES = (
    "agree", "agreed", "yes", "ok", "okay", "sure", "consensus", "final", "settled",
    "haan", "sahi", "theek", "thik", "bilkul", "mutfiq",
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _parse_ts(ts: Any) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _speaker(msg: Dict[str, Any]) -> Optional[str]:
    return msg.get("username") or msg.get("sender")


def student_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Time-ordered student messages (Moderator/System excluded)."""
    msgs = [m for m in (messages or []) if _speaker(m) not in _SKIP]
    return sorted(msgs, key=lambda m: m.get("created_at") or "")


def build_turns(s_msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse consecutive same-speaker messages into TURNS.

    Each turn: {speaker, start, end (datetime), message_ids, count}.
    """
    turns: List[Dict[str, Any]] = []
    for m in s_msgs:
        spk = _speaker(m)
        ts = _parse_ts(m.get("created_at"))
        mid = str(m.get("id")) if m.get("id") is not None else None
        if turns and turns[-1]["speaker"] == spk:
            t = turns[-1]
            t["count"] += 1
            if mid:
                t["message_ids"].append(mid)
            if ts:
                t["end"] = ts
        else:
            turns.append({
                "speaker": spk,
                "start": ts,
                "end": ts,
                "count": 1,
                "message_ids": [mid] if mid else [],
            })
    return turns


# ------------------------------------------------------------
# 1. Turn counts
# ------------------------------------------------------------
def turn_metrics(s_msgs: List[Dict[str, Any]], students: List[str]) -> Dict[str, Any]:
    """LOCKED DEFINITION (8.5): a TURN is a maximal run of consecutive messages by the
    same student. turn_count(participant) = number of such runs they own; room turn_count
    = total runs. This definition is final and must not change once data collection begins.
    """
    turns = build_turns(s_msgs)
    per = {u: 0 for u in students}
    for t in turns:
        if t["speaker"] in per:
            per[t["speaker"]] += 1
        else:
            per[t["speaker"]] = per.get(t["speaker"], 0) + 1
    return {"room_turn_count": len(turns), "turns_per_participant": per}


# ------------------------------------------------------------
# 2/3. Speaking-time + share + average turn duration (needs durations)
# ------------------------------------------------------------
def duration_metrics(
    s_msgs: List[Dict[str, Any]],
    durations: Optional[Dict[str, int]],
    students: List[str],
) -> Dict[str, Any]:
    """LOCKED DEFINITION (8.5): speaking_time_share is derived ONLY from
    voice_recordings.duration_ms (real spoken audio length) — never from text length,
    message counts, or timestamps. When no durations exist the shares are 0 and
    durations_available is False; they must NOT be back-filled from other signals.
    """
    durations = durations or {}
    have_any = bool(durations)
    time_per = {u: 0 for u in students}
    known_turn_durations: List[float] = []
    turn_dur_per: Dict[str, List[float]] = {u: [] for u in students}

    # per-message speaking time
    for m in s_msgs:
        mid = str(m.get("id")) if m.get("id") is not None else None
        spk = _speaker(m)
        d = durations.get(mid) if mid else None
        if d is not None and spk is not None:
            time_per[spk] = time_per.get(spk, 0) + int(d)

    # per-turn duration (sum of its messages' known durations)
    for t in build_turns(s_msgs):
        td = sum(int(durations[mid]) for mid in t["message_ids"] if mid in durations)
        if td > 0:
            known_turn_durations.append(td)
            turn_dur_per.setdefault(t["speaker"], []).append(td)

    total_time = sum(time_per.values())
    share = {u: (time_per[u] / total_time if total_time else 0.0) for u in time_per}
    avg_turn_dur = (sum(known_turn_durations) / len(known_turn_durations)) if known_turn_durations else None
    avg_turn_dur_per = {
        u: (sum(v) / len(v) if v else None) for u, v in turn_dur_per.items()
    }
    return {
        "durations_available": have_any and total_time > 0,
        "speaking_time_ms_per_participant": time_per,
        "speaking_time_share": share,            # 0..1; None-equivalent when no durations
        "total_speaking_time_ms": total_time,
        "avg_turn_duration_ms": avg_turn_dur,    # None when no durations
        "avg_turn_duration_ms_per_participant": avg_turn_dur_per,
    }


# ------------------------------------------------------------
# 4. Silence between turns
# ------------------------------------------------------------
def silence_metrics(s_msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    turns = [t for t in build_turns(s_msgs) if t["start"] and t["end"]]
    gaps: List[float] = []
    for prev, nxt in zip(turns, turns[1:]):
        g = (nxt["start"] - prev["end"]).total_seconds()
        if g >= 0:
            gaps.append(g)
    return {
        "longest_silence_sec": max(gaps) if gaps else None,
        "avg_silence_sec": (sum(gaps) / len(gaps)) if gaps else None,
        "silence_gap_count": len(gaps),
    }


# ------------------------------------------------------------
# 5. Moderator response latency (trigger → intervention)
# ------------------------------------------------------------
def moderator_latency(
    s_msgs: List[Dict[str, Any]],
    interventions: List[Dict[str, Any]],
    *,
    max_window_sec: float = 600.0,
) -> Dict[str, Any]:
    """Seconds between the triggering student message and the moderator's intervention.

    For each intervention we take the most recent preceding student message as the
    trigger; latency = intervention_time − trigger_time (capped to a window to avoid
    session-start artifacts). Reported as mean + median.
    """
    stud_times = sorted(t for t in (_parse_ts(m.get("created_at")) for m in s_msgs) if t)
    lat: List[float] = []
    for inv in interventions or []:
        t_iv = _parse_ts(inv.get("timestamp"))
        if not t_iv:
            continue
        trigger = None
        for t in stud_times:
            if t <= t_iv:
                trigger = t
            else:
                break
        if trigger is not None:
            delta = (t_iv - trigger).total_seconds()
            if 0 <= delta <= max_window_sec:
                lat.append(delta)
    return {
        "count": len(lat),
        "mean_latency_sec": (sum(lat) / len(lat)) if lat else None,
        "median_latency_sec": _median(lat),
    }


# ------------------------------------------------------------
# 6. Intervention frequency
# ------------------------------------------------------------
def intervention_frequency(
    interventions: List[Dict[str, Any]], session_minutes: float
) -> Dict[str, Any]:
    by_type: Dict[str, int] = {}
    for inv in interventions or []:
        k = str(inv.get("intervention_type") or "unknown")
        by_type[k] = by_type.get(k, 0) + 1
    total = sum(by_type.values())
    per_min = (total / session_minutes) if session_minutes and session_minutes > 0 else None
    return {
        "intervention_count": total,
        "interventions_per_minute": per_min,
        "interventions_by_type": by_type,
    }


# ------------------------------------------------------------
# 7. Consensus progress over time (documented lexical PROXY)
# ------------------------------------------------------------
def consensus_timeline(
    s_msgs: List[Dict[str, Any]],
    *,
    bucket_sec: float = 120.0,
    session_start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Per-bucket agreement-cue density among student messages (0..1).

    LOCKED LABEL (8.5): this is a PROXY — deterministic and reproducible, but purely
    lexical. It MUST always be reported as "consensus_proxy" and NEVER claimed as a
    ground-truth consensus measure. The validated consensus signal comes from the
    session-summary pipeline (P4). Buckets are bucket_sec wide from the first message.
    """
    first_ts = next((_parse_ts(m.get("created_at")) for m in s_msgs if _parse_ts(m.get("created_at"))), None)
    t0 = session_start or first_ts
    if t0 is None:
        return []
    # Tag agreement cues per time bucket at the message level.
    series_num: Dict[int, int] = {}
    series_den: Dict[int, int] = {}
    for m in s_msgs:
        ts = _parse_ts(m.get("created_at"))
        if not ts:
            continue
        idx = max(0, int((ts - t0).total_seconds() // bucket_sec))
        series_den[idx] = series_den.get(idx, 0) + 1
        text = (m.get("message") or "").lower()
        if any(c in text for c in _AGREEMENT_CUES):
            series_num[idx] = series_num.get(idx, 0) + 1
    out = []
    for idx in sorted(series_den):
        den = series_den[idx]
        num = series_num.get(idx, 0)
        out.append({
            "bucket_index": idx,
            "t_start_sec": idx * bucket_sec,
            "consensus_proxy": round(num / den, 3) if den else 0.0,
            "student_messages": den,
        })
    return out


# ------------------------------------------------------------
# 8. Participation balance (turns + time)
# ------------------------------------------------------------
def participation_balance(
    turns_per_participant: Dict[str, int],
    speaking_time_per_participant: Dict[str, int],
) -> Dict[str, Any]:
    turn_counts = list(turns_per_participant.values())
    turn_total = sum(turn_counts)
    turn_shares = [c / turn_total for c in turn_counts] if turn_total else [0.0 for _ in turn_counts]

    time_vals = list(speaking_time_per_participant.values())
    time_total = sum(time_vals)
    time_shares = [v / time_total for v in time_vals] if time_total else None

    return {
        "turn_gini": calculate_gini_coefficient(turn_shares),
        "turn_entropy": calculate_entropy(turn_shares),
        "turn_dominance_gap": (max(turn_shares) - min(turn_shares)) if turn_shares else 0.0,
        "time_gini": calculate_gini_coefficient(time_shares) if time_shares else None,
        "time_entropy": calculate_entropy(time_shares) if time_shares else None,
    }


# ------------------------------------------------------------
# 9. Interruption estimate
# ------------------------------------------------------------
def interruption_estimate(s_msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rapid speaker-switches within INTERRUPTION_GAP_SEC (overlap proxy)."""
    rapid = 0
    prev_spk = None
    prev_ts = None
    for m in s_msgs:
        spk = _speaker(m)
        ts = _parse_ts(m.get("created_at"))
        if prev_spk and spk and spk != prev_spk and prev_ts and ts:
            if 0 <= (ts - prev_ts).total_seconds() < INTERRUPTION_GAP_SEC:
                rapid += 1
        prev_spk, prev_ts = spk, ts
    return {"interruption_estimate": rapid, "gap_threshold_sec": INTERRUPTION_GAP_SEC}


def _median(xs: List[float]) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    mid = len(s) // 2
    return float(s[mid]) if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0


# ------------------------------------------------------------
# Visualization timelines (PART 4) — clean JSON, no charting here.
# ------------------------------------------------------------
def _first_ts(s_msgs: List[Dict[str, Any]]) -> Optional[datetime]:
    return next((_parse_ts(m.get("created_at")) for m in s_msgs if _parse_ts(m.get("created_at"))), None)


def speaking_share_timeline(
    s_msgs: List[Dict[str, Any]],
    durations: Optional[Dict[str, int]],
    students: List[str],
    *,
    bucket_sec: float = 60.0,
    session_start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Per-bucket speaking-time share per participant (falls back to message-count
    share when audio durations are unavailable)."""
    durations = durations or {}
    t0 = session_start or _first_ts(s_msgs)
    if t0 is None:
        return []
    use_time = bool(durations)
    buckets: Dict[int, Dict[str, float]] = {}
    for m in s_msgs:
        ts = _parse_ts(m.get("created_at"))
        spk = _speaker(m)
        if not ts or spk not in students:
            continue
        idx = max(0, int((ts - t0).total_seconds() // bucket_sec))
        mid = str(m.get("id")) if m.get("id") is not None else None
        w = float(durations.get(mid, 0)) if use_time else 1.0
        if use_time and w == 0:
            continue
        buckets.setdefault(idx, {u: 0.0 for u in students})[spk] += w
    out = []
    for idx in sorted(buckets):
        vals = buckets[idx]
        tot = sum(vals.values()) or 1.0
        out.append({
            "bucket_index": idx,
            "t_start_sec": idx * bucket_sec,
            "shares": {u: round(vals[u] / tot, 4) for u in students},
            "basis": "speaking_time" if use_time else "message_count",
        })
    return out


def participation_timeline(
    s_msgs: List[Dict[str, Any]],
    students: List[str],
    *,
    bucket_sec: float = 60.0,
    session_start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Per-bucket message-count share per participant (turn-taking view)."""
    return speaking_share_timeline(s_msgs, None, students, bucket_sec=bucket_sec, session_start=session_start)


def intervention_timeline(
    interventions: List[Dict[str, Any]],
    *,
    bucket_sec: float = 60.0,
    session_start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Per-bucket intervention counts by type."""
    rows = [(_parse_ts(i.get("timestamp")), str(i.get("intervention_type") or "unknown"))
            for i in (interventions or [])]
    rows = [(t, k) for t, k in rows if t]
    if not rows:
        return []
    t0 = session_start or min(t for t, _ in rows)
    buckets: Dict[int, Dict[str, int]] = {}
    for t, k in rows:
        idx = max(0, int((t - t0).total_seconds() // bucket_sec))
        b = buckets.setdefault(idx, {})
        b[k] = b.get(k, 0) + 1
    return [
        {"bucket_index": idx, "t_start_sec": idx * bucket_sec,
         "by_type": buckets[idx], "total": sum(buckets[idx].values())}
        for idx in sorted(buckets)
    ]


# ------------------------------------------------------------
# Top-level: compute everything
# ------------------------------------------------------------
def compute_all(
    room_id: str,
    messages: List[Dict[str, Any]],
    *,
    interventions: Optional[List[Dict[str, Any]]] = None,
    durations: Optional[Dict[str, int]] = None,
    students: Optional[List[str]] = None,
    condition: Optional[str] = None,
    session_started_at: Optional[str] = None,
    session_ended_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the full authoritative metric set for a room.

    Returns {"participants": [...], "room_summary": {...}, "timelines": {...}}.
    Robust to empty rooms, single participants, and missing durations.
    """
    s_msgs = student_messages(messages)
    if students is None:
        students = sorted({s for s in (_speaker(m) for m in s_msgs) if s not in _SKIP})
    students = [s for s in students if s not in _SKIP]

    tm = turn_metrics(s_msgs, students)
    dm = duration_metrics(s_msgs, durations, students)
    sm = silence_metrics(s_msgs)
    lat = moderator_latency(s_msgs, interventions or [])
    bal = participation_balance(tm["turns_per_participant"], dm["speaking_time_ms_per_participant"])
    ir = interruption_estimate(s_msgs)

    # Session duration (minutes) from explicit session bounds, else message span.
    start = _parse_ts(session_started_at)
    end = _parse_ts(session_ended_at)
    if not start and s_msgs:
        start = _parse_ts(s_msgs[0].get("created_at"))
    if not end and s_msgs:
        end = _parse_ts(s_msgs[-1].get("created_at"))
    session_minutes = ((end - start).total_seconds() / 60.0) if (start and end) else 0.0

    ifreq = intervention_frequency(interventions or [], session_minutes)
    timeline = consensus_timeline(s_msgs, session_start=start)
    speaking_tl = speaking_share_timeline(s_msgs, durations, students, session_start=start)
    participation_tl = participation_timeline(s_msgs, students, session_start=start)
    intervention_tl = intervention_timeline(interventions or [], session_start=start)

    # Per-participant message + WORD counts. Word share is the PRIMARY participation-
    # equality basis for this study (Gini on word share), per the research design.
    msg_counts = {u: 0 for u in students}
    word_counts = {u: 0 for u in students}
    for m in s_msgs:
        spk = _speaker(m)
        if spk in msg_counts:
            msg_counts[spk] += 1
            word_counts[spk] += len((m.get("message") or "").split())
    total_words = sum(word_counts.values())
    word_shares_map = {u: (word_counts[u] / total_words if total_words else 0.0) for u in students}
    word_share_list = list(word_shares_map.values())
    word_gini = calculate_gini_coefficient(word_share_list)
    word_entropy = calculate_entropy(word_share_list)
    word_dominance_gap = (max(word_share_list) - min(word_share_list)) if word_share_list else 0.0

    turn_total = tm["room_turn_count"] or 1
    participants = []
    for u in students:
        participants.append({
            "participant_id": u,
            "message_count": msg_counts.get(u, 0),
            "word_count": word_counts.get(u, 0),
            "word_share": round(word_shares_map.get(u, 0.0), 4),
            "turn_count": tm["turns_per_participant"].get(u, 0),
            "turn_share": round(tm["turns_per_participant"].get(u, 0) / turn_total, 4),
            "speaking_time_ms": dm["speaking_time_ms_per_participant"].get(u, 0),
            "speaking_time_share": round(dm["speaking_time_share"].get(u, 0.0), 4),
            "avg_turn_duration_ms": dm["avg_turn_duration_ms_per_participant"].get(u),
        })

    room_summary = {
        "room_id": room_id,
        "condition": condition,
        "participant_count": len(students),
        "total_student_messages": len(s_msgs),
        "total_words": total_words,
        "session_minutes": round(session_minutes, 2),
        # participation equality — WORD-share Gini is the PRIMARY measure (study design);
        # turn- and time-share variants are kept for secondary/robustness analysis.
        "word_gini": word_gini,
        "word_entropy": word_entropy,
        "word_dominance_gap": word_dominance_gap,
        "turn_gini": bal["turn_gini"],
        "turn_entropy": bal["turn_entropy"],
        "dominance_gap": bal["turn_dominance_gap"],
        "time_gini": bal["time_gini"],
        "time_entropy": bal["time_entropy"],
        # turns / timing
        "turn_count": tm["room_turn_count"],
        "avg_turn_duration_ms": dm["avg_turn_duration_ms"],
        "longest_silence_sec": sm["longest_silence_sec"],
        "avg_silence_sec": sm["avg_silence_sec"],
        "durations_available": dm["durations_available"],
        # moderator
        "intervention_count": ifreq["intervention_count"],
        "interventions_per_minute": ifreq["interventions_per_minute"],
        "interventions_by_type": ifreq["interventions_by_type"],
        "moderator_mean_latency_sec": lat["mean_latency_sec"],
        "moderator_median_latency_sec": lat["median_latency_sec"],
        # interaction
        "interruption_estimate": ir["interruption_estimate"],
        # consensus (proxy — see consensus_timeline docstring)
        "consensus_proxy_final": timeline[-1]["consensus_proxy"] if timeline else None,
    }

    return {
        "participants": participants,
        "room_summary": room_summary,
        "timelines": {
            "consensus_timeline": timeline,
            "speaking_share_timeline": speaking_tl,
            "participation_timeline": participation_tl,
            "intervention_timeline": intervention_tl,
        },
    }
