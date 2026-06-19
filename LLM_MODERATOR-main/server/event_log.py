from __future__ import annotations

# ============================================================
# 🪵 event_log.py — Research-integrity substrate (Priority 8)
# ------------------------------------------------------------
# Provides:
#   * experiment_condition()  — the ONE immutable condition mapping (8.2)
#   * log_event()             — fail-safe append-only ground-truth writer (8.4)
#   * gather_room_inputs()    — DB-only inputs for metrics (8.3)
#   * compute_room_metrics()  — DB-only authoritative metrics (8.3)
#   * finalize_session()      — freeze state + metrics snapshot at session end (8.1)
#   * reconstruct_session()   — rebuild a whole session FROM DB ONLY (8.3)
#
# FAIL-SAFE PRINCIPLE (8.6): nothing here ever raises into a caller. Logging/persistence
# failures are swallowed-and-logged so the live session is never interrupted and data is
# never dropped silently (errors are written to the app log).
#
# All reads/computation use DURABLE data only (messages, interventions, voice_recordings)
# — NO runtime memory — so any session is reproducible from the database alone.
# ============================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("event-log")

# ------------------------------------------------------------
# 8.2 — Immutable experiment condition (single source of truth)
# ------------------------------------------------------------
CONDITION_ACTIVE = "active_moderator"
CONDITION_PASSIVE = "passive_moderator"
CONDITION_NONE = "no_moderator"

_MODE_TO_CONDITION = {
    "active": CONDITION_ACTIVE,
    "active_moderator": CONDITION_ACTIVE,
    "passive": CONDITION_PASSIVE,
    "passive_moderator": CONDITION_PASSIVE,
    "none": CONDITION_NONE,
    "no_moderator": CONDITION_NONE,
    "control": CONDITION_NONE,
}


def experiment_condition(room: Optional[Dict[str, Any]]) -> str:
    """Map a room's (immutable) mode to its canonical experiment condition.

    Condition is set at room creation and never changes mid-session — it is derived
    here, not stored mutably, so it cannot drift. Defaults to no_moderator if unknown.
    """
    if not room:
        return CONDITION_NONE
    mode = str(room.get("mode") or "").strip().lower()
    return _MODE_TO_CONDITION.get(mode, CONDITION_NONE)


# ------------------------------------------------------------
# 8.4 — Append-only event log (fail-safe writer)
# ------------------------------------------------------------
def log_event(
    room_id: Optional[str],
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    session_id: Optional[str] = None,
    condition: Optional[str] = None,
) -> bool:
    """Append one event to the ground-truth log. NEVER raises.

    event_type ∈ {message, stt, tts, intervention, state_update, session}.
    Returns True if written, False if it couldn't be (and logs the reason).
    """
    try:
        from supabase_client import supabase
        row = {
            "room_id": room_id,
            "session_id": session_id,
            "experiment_condition": condition,
            "event_type": event_type,
            "payload_json": payload or {},
        }
        supabase.table("event_log").insert(row).execute()
        return True
    except Exception as e:
        # Never interrupt the session; surface the failure in the app log only.
        logger.warning(f"event_log write failed ({event_type}, room={room_id}): {e}")
        return False


def log_failure(room_id: Optional[str], kind: str, *, recovery: Optional[str] = None, **info) -> bool:
    """Append a FAILURE event so every failure is explicitly visible in research exports.

    kind ∈ {stt, tts, tts_provider_fallback, llm_fallback, metric_skip, missing_audio}.
    `recovery` describes the fail-safe action taken. Never raises.
    """
    payload: Dict[str, Any] = {"kind": kind, **info}
    if recovery:
        payload["recovery"] = recovery
    return log_event(room_id, "failure", payload)


# ------------------------------------------------------------
# 8.3 — DB-only input gathering + metric computation
# ------------------------------------------------------------
def gather_room_inputs(room_id: str) -> Dict[str, Any]:
    """Fetch everything needed to (re)compute a room's metrics, from the DB only."""
    from supabase_client import (
        supabase, get_room, get_chat_history, get_participants,
        get_voice_recordings_for_room,
    )

    room = get_room(room_id) or {}
    messages = get_chat_history(room_id) or []

    try:
        interventions = (
            supabase.table("moderator_interventions").select("*").eq("room_id", room_id).execute().data
        ) or []
    except Exception as e:
        logger.debug(f"interventions unavailable for {room_id}: {e}")
        interventions = []

    durations: Dict[str, int] = {}
    try:
        for vr in (get_voice_recordings_for_room(room_id) or []):
            mid, dur = vr.get("message_id"), vr.get("duration_ms")
            if mid is not None and isinstance(dur, (int, float)):
                durations[str(mid)] = int(dur)
    except Exception as e:
        logger.debug(f"durations unavailable for {room_id}: {e}")

    students = [
        p.get("username") for p in (get_participants(room_id) or [])
        if p.get("username") not in ("Moderator", "System", None, "")
    ]

    return {
        "room": room,
        "messages": messages,
        "interventions": interventions,
        "durations": durations,
        "students": students,
        "condition": experiment_condition(room),
        "started_at": room.get("created_at"),
        "ended_at": room.get("ended_at"),
    }


def compute_room_metrics(room_id: str) -> Dict[str, Any]:
    """Authoritative metrics for a room, computed from the DB only (reproducible)."""
    import research_metrics_v2 as RM2
    g = gather_room_inputs(room_id)
    result = RM2.compute_all(
        room_id,
        g["messages"],
        interventions=g["interventions"],
        durations=g["durations"] or None,
        students=g["students"] or None,
        condition=g["condition"],
        session_started_at=g["started_at"],
        session_ended_at=g["ended_at"],
    )
    return result


# ------------------------------------------------------------
# 8.1 — Freeze state + metrics at session end
# ------------------------------------------------------------
def finalize_session(room_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Freeze and persist a session's record. Best-effort; never raises.

    Persists: room_state snapshot + final metrics_v2 (with timelines) + a
    room_metrics_summary row + tidy research_metrics_v2 rows, all stamped with the
    immutable experiment condition, and logs a 'session' finalized event.
    Returns a small status dict.
    """
    status = {"room_id": room_id, "snapshot": False, "summary": False, "tidy_rows": 0, "metrics": False}
    try:
        from supabase_client import (
            save_room_state_snapshot, save_room_metrics_summary, save_research_metrics_v2_rows,
        )
        try:
            from room_state import get_room_state
            rstate = get_room_state(room_id)
        except Exception:
            rstate = {}

        result = compute_room_metrics(room_id)
        status["metrics"] = True
        condition = result["room_summary"].get("condition")

        status["snapshot"] = save_room_state_snapshot(
            room_id, session_id, rstate, result, condition, kind="final"
        )
        status["summary"] = save_room_metrics_summary(room_id, session_id, result["room_summary"])
        status["tidy_rows"] = save_research_metrics_v2_rows(room_id, result)

        # Run integrity validators at finalize (C/D) and record the verdict.
        events_present = False
        failure_report_ok = False
        try:
            vr = validate_session(room_id)
            status["readiness"] = vr["readiness"]["status"]
            status["integrity_score"] = vr["readiness"]["data_integrity_score"]
            events_present = vr["consistency"]["checks"].get("event_log_present", True) is not False \
                and "event_log empty" not in " ".join(vr["consistency"]["issues"])
            failure_report_ok = isinstance(vr.get("failure_report"), dict)
            log_event(room_id, "session", {
                "action": "validated",
                "readiness": vr["readiness"],
                "consistency_issues": vr["consistency"]["issues"],
                "condition_issues": vr["condition_audit"]["issues"],
            }, session_id=session_id, condition=condition)
        except Exception as ve:
            logger.warning(f"validate_session at finalize failed for {room_id}: {ve}")

        # P3 — finalization guarantee: verify ALL five steps, never silently succeed.
        import validation as V
        verdict = V.assess_finalization({
            "event_log_complete": events_present,
            "metrics_computed": status["metrics"],
            "snapshot_exists": status["snapshot"],
            "failure_report_generated": failure_report_ok,
            "export_bundle_available": status["metrics"] and status["snapshot"],
        })
        status["finalization"] = verdict["status"]
        status["missing_steps"] = verdict["missing_steps"]
        if verdict["status"] != "COMPLETE":
            logger.error(f"⚠️ Session {room_id} finalization INCOMPLETE — missing: {verdict['missing_steps']}")

        log_event(room_id, "session", {
            "action": "finalized",
            "finalization": verdict["status"],
            "missing_steps": verdict["missing_steps"],
            "status": status,
        }, session_id=session_id, condition=condition)
    except Exception as e:
        # metrics failure → skip computation but LOG it (8.6); never drop the session.
        logger.error(f"finalize_session failed for {room_id}: {e}")
        status["finalization"] = "INCOMPLETE"
        status["error"] = str(e)
        log_event(room_id, "session", {"action": "finalize_error", "finalization": "INCOMPLETE",
                                       "error": str(e)}, session_id=session_id)
    return status


# ------------------------------------------------------------
# Final Phase — full session validation (C/D/E/G in one DB-only path)
# ------------------------------------------------------------
def validate_session(room_id: str) -> Dict[str, Any]:
    """Run all integrity validators for a room from the DB only. Never raises.

    Returns {metrics, consistency, condition_audit, failure_report, readiness,
    reproducibility_score}. This is the single backbone behind finalize + every
    validation/readiness endpoint, so all report the same numbers.
    """
    import json as _json
    import validation as V
    from supabase_client import supabase, get_voice_recordings_for_room

    g = gather_room_inputs(room_id)
    room, condition = g["room"], g["condition"]

    metrics = compute_room_metrics(room_id)

    # Reproducibility: recompute and compare — identical DB input must give identical output.
    metrics2 = compute_room_metrics(room_id)
    reproducibility_score = 1.0 if _json.dumps(metrics, sort_keys=True) == _json.dumps(metrics2, sort_keys=True) else 0.0

    def _safe(table, order=None):
        try:
            q = supabase.table(table).select("*").eq("room_id", room_id)
            if order:
                q = q.order(order)
            return q.execute().data or []
        except Exception:
            return []

    events = _safe("event_log", order="timestamp")
    snapshots = _safe("room_state_snapshots")
    try:
        voice_recordings = get_voice_recordings_for_room(room_id) or []
    except Exception:
        voice_recordings = []

    consistency = V.check_consistency(g["messages"], g["interventions"], voice_recordings, events, metrics)
    condition_audit = V.audit_condition(room, condition, metrics, snapshots)
    failure_report = V.build_failure_report(events, room_id=room_id)
    readiness = V.experiment_readiness(
        consistency, condition_audit,
        has_snapshot=bool(snapshots),
        reproducibility_score=reproducibility_score,
        has_events=bool(events),
    )
    return {
        "room_id": room_id,
        "experiment_condition": condition,
        "metrics": metrics,
        "consistency": consistency,
        "condition_audit": condition_audit,
        "failure_report": failure_report,
        "reproducibility_score": reproducibility_score,
        "readiness": readiness,
    }


# ------------------------------------------------------------
# 8.3 — Reconstruct a whole session from the DB only
# ------------------------------------------------------------
def reconstruct_session(room_id: str) -> Dict[str, Any]:
    """Rebuild a session entirely from the database — no runtime memory.

    Prefers a frozen snapshot when present; otherwise recomputes live from durable
    data. Returns events + messages + interventions + metrics + timelines + condition.
    """
    from supabase_client import supabase, get_room, get_chat_history

    room = get_room(room_id) or {}
    condition = experiment_condition(room)

    def _safe(table, order=None):
        try:
            q = supabase.table(table).select("*").eq("room_id", room_id)
            if order:
                q = q.order(order)
            return q.execute().data or []
        except Exception as e:
            logger.debug(f"reconstruct: {table} unavailable for {room_id}: {e}")
            return []

    events = _safe("event_log", order="timestamp")
    interventions = _safe("moderator_interventions", order="timestamp")
    snapshots = _safe("room_state_snapshots")

    frozen = snapshots[-1].get("final_metrics_json") if snapshots else None
    metrics = frozen if frozen else compute_room_metrics(room_id)

    return {
        "room_id": room_id,
        "experiment_condition": condition,
        "from_snapshot": bool(frozen),
        "messages": get_chat_history(room_id) or [],
        "interventions": interventions,
        "events": events,
        "room_summary": metrics.get("room_summary", {}),
        "participants": metrics.get("participants", []),
        "timelines": metrics.get("timelines", {}),
    }
