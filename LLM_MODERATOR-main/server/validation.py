from __future__ import annotations

# ============================================================
# ✅ validation.py — Experiment-integrity validators (Final Phase)
# ------------------------------------------------------------
# Pure, deterministic checks over DURABLE data (no runtime memory, no AI). Used at
# session finalize, admin export, and the readiness endpoint.
#
#   * check_consistency()     — C: event-log/metrics/timeline/voice consistency
#   * audit_condition()       — D: condition assigned, immutable, consistent
#   * build_failure_report()  — E: failures explicitly surfaced from the event log
#   * experiment_readiness()  — G: PASS/FAIL + integrity + reproducibility scores
#
# These functions take already-gathered data dicts so they are trivially testable and
# identical across runs given identical input (reproducibility requirement).
# ============================================================

from typing import Any, Dict, List, Optional

_SKIP = {"Moderator", "System", None, ""}


def _speaker(m: Dict[str, Any]) -> Optional[str]:
    return m.get("username") or m.get("sender")


def _is_voice(m: Dict[str, Any]) -> bool:
    meta = m.get("metadata")
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    if isinstance(meta, dict) and meta.get("input_mode") == "voice":
        return True
    return m.get("input_mode") == "voice"


def derive_turn_count(messages: List[Dict[str, Any]]) -> int:
    """Independent turn count (maximal same-speaker runs), recomputed from messages.

    Mirrors research_metrics_v2.build_turns so we can cross-check the metric.
    """
    s = [m for m in (messages or []) if _speaker(m) not in _SKIP]
    s.sort(key=lambda m: m.get("created_at") or "")
    turns = 0
    last = object()
    for m in s:
        spk = _speaker(m)
        if spk != last:
            turns += 1
            last = spk
    return turns


# ------------------------------------------------------------
# C — Data consistency validator
# ------------------------------------------------------------
def check_consistency(
    messages: List[Dict[str, Any]],
    interventions: List[Dict[str, Any]],
    voice_recordings: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Return {checks, issues, integrity_score, passed}. Deterministic."""
    issues: List[str] = []
    checks: Dict[str, bool] = {}

    s_msgs = [m for m in (messages or []) if _speaker(m) not in _SKIP]

    # 1) metrics turn_count == event-derived turn count
    derived_turns = derive_turn_count(messages)
    metric_turns = (metrics or {}).get("room_summary", {}).get("turn_count")
    checks["turn_count_matches"] = (metric_turns == derived_turns)
    if not checks["turn_count_matches"]:
        issues.append(f"turn_count mismatch: metric={metric_turns} derived={derived_turns}")

    # 2) timeline consistency — every student message has a parseable timestamp
    missing_ts = sum(1 for m in s_msgs if not m.get("created_at"))
    checks["all_timestamps_present"] = (missing_ts == 0)
    if missing_ts:
        issues.append(f"{missing_ts} student message(s) missing created_at")

    # 3) voice_recordings ↔ voice messages (1:1)
    voice_msg_ids = {str(m.get("id")) for m in s_msgs if _is_voice(m) and m.get("id") is not None}
    vr_msg_ids = {str(v.get("message_id")) for v in (voice_recordings or []) if v.get("message_id") is not None}
    checks["voice_one_to_one"] = (voice_msg_ids == vr_msg_ids)
    if not checks["voice_one_to_one"]:
        missing = voice_msg_ids - vr_msg_ids
        extra = vr_msg_ids - voice_msg_ids
        if missing:
            issues.append(f"{len(missing)} voice message(s) without a recording")
        if extra:
            issues.append(f"{len(extra)} recording(s) with no matching voice message")

    # 4) event-log completeness — a message/intervention event per row (when log exists)
    if events:
        msg_events = sum(1 for e in events if e.get("event_type") == "message")
        iv_events = sum(1 for e in events if e.get("event_type") == "intervention")
        checks["message_events_complete"] = msg_events >= len(s_msgs)
        checks["intervention_events_complete"] = iv_events >= len(interventions or [])
        if not checks["message_events_complete"]:
            issues.append(f"message events {msg_events} < messages {len(s_msgs)}")
        if not checks["intervention_events_complete"]:
            issues.append(f"intervention events {iv_events} < interventions {len(interventions or [])}")

        # 5) no orphaned message events (referencing a non-existent message id)
        msg_ids = {str(m.get("id")) for m in messages if m.get("id") is not None}
        orphans = 0
        for e in events:
            if e.get("event_type") == "message":
                mid = (e.get("payload_json") or {}).get("message_id")
                if mid and mid not in msg_ids:
                    orphans += 1
        checks["no_orphaned_events"] = (orphans == 0)
        if orphans:
            issues.append(f"{orphans} orphaned message event(s)")
    else:
        checks["event_log_present"] = False
        issues.append("event_log empty (migration 006 not applied or no events written)")

    passed_checks = sum(1 for v in checks.values() if v)
    integrity_score = round(passed_checks / len(checks), 3) if checks else 0.0
    return {
        "checks": checks,
        "issues": issues,
        "integrity_score": integrity_score,
        "passed": len(issues) == 0,
    }


# ------------------------------------------------------------
# D — Experiment condition audit
# ------------------------------------------------------------
def audit_condition(
    room: Dict[str, Any],
    expected_condition: str,
    metrics: Dict[str, Any],
    snapshots: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Confirm the condition was assigned at creation, never drifted, and is consistent
    across metrics + snapshots. Rejects on any drift."""
    issues: List[str] = []
    assigned_at_creation = bool(room and room.get("mode"))
    if not assigned_at_creation:
        issues.append("room has no mode/condition assigned at creation")

    metric_cond = (metrics or {}).get("room_summary", {}).get("condition")
    if metric_cond and metric_cond != expected_condition:
        issues.append(f"metrics condition {metric_cond} != expected {expected_condition}")

    snap_conds = {s.get("experiment_condition") for s in (snapshots or []) if s.get("experiment_condition")}
    drift = any(c != expected_condition for c in snap_conds)
    if drift:
        issues.append(f"snapshot condition drift: {sorted(snap_conds)} vs {expected_condition}")

    return {
        "expected_condition": expected_condition,
        "assigned_at_creation": assigned_at_creation,
        "condition_drift_detected": drift or any("!=" in i for i in issues),
        "issues": issues,
        "passed": len(issues) == 0,
    }


# ------------------------------------------------------------
# E — Failure trace report (from the event log)
# ------------------------------------------------------------
def build_failure_report(events: List[Dict[str, Any]], room_id: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate failure/fallback events into an explicit, exportable report."""
    report = {
        "room_id": room_id,
        "stt_failures": [],
        "tts_failures": [],
        "llm_fallbacks": [],
        "metric_skips": [],
        "missing_audio": [],
        "recovery_actions": [],
        "total_failures": 0,
    }
    for e in (events or []):
        if e.get("event_type") != "failure":
            continue
        p = e.get("payload_json") or {}
        kind = str(p.get("kind") or "")
        entry = {"timestamp": e.get("timestamp"), **p}
        if kind == "stt":
            report["stt_failures"].append(entry)
        elif kind == "tts":
            report["tts_failures"].append(entry)
        elif kind in ("llm_fallback", "tts_provider_fallback"):
            report["llm_fallbacks"].append(entry)
        elif kind == "metric_skip":
            report["metric_skips"].append(entry)
        elif kind == "missing_audio":
            report["missing_audio"].append(entry)
        if p.get("recovery"):
            report["recovery_actions"].append({"timestamp": e.get("timestamp"), "action": p.get("recovery")})
    report["total_failures"] = (
        len(report["stt_failures"]) + len(report["tts_failures"]) +
        len(report["llm_fallbacks"]) + len(report["metric_skips"]) + len(report["missing_audio"])
    )
    return report


# ------------------------------------------------------------
# P3 — Session finalization guarantee (COMPLETE vs INCOMPLETE)
# ------------------------------------------------------------
# The five steps that MUST succeed at session end. Anything missing => INCOMPLETE.
FINALIZATION_STEPS = (
    "event_log_complete",
    "metrics_computed",
    "snapshot_exists",
    "failure_report_generated",
    "export_bundle_available",
)


def assess_finalization(steps: Dict[str, bool]) -> Dict[str, Any]:
    """Verdict for the finalization guarantee. NEVER silently succeeds.

    `steps` maps each FINALIZATION_STEPS key to a bool. Returns status COMPLETE only
    when ALL required steps passed; otherwise INCOMPLETE with the missing steps listed.
    """
    missing = [k for k in FINALIZATION_STEPS if not steps.get(k)]
    return {
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "steps": {k: bool(steps.get(k)) for k in FINALIZATION_STEPS},
        "missing_steps": missing,
    }


# ------------------------------------------------------------
# P2 — Passive moderator constraint audit
# ------------------------------------------------------------
def audit_passive_constraints(condition: str, interventions: List[Dict[str, Any]],
                              allowed: set) -> Dict[str, Any]:
    """For the passive condition, every intervention type MUST be in the allowed set
    (direct mention / final time warning / safety only). Reports any violations."""
    if condition != "passive_moderator":
        return {"applicable": False, "passed": True, "violations": []}
    violations = sorted({
        str(i.get("intervention_type"))
        for i in (interventions or [])
        if str(i.get("intervention_type")) not in allowed
    })
    return {"applicable": True, "passed": not violations, "violations": violations,
            "allowed": sorted(allowed)}


# ------------------------------------------------------------
# P3/P6 — Dataset schema completeness
# ------------------------------------------------------------
def check_schema_completeness(metrics: Dict[str, Any], locked_metric_names) -> Dict[str, Any]:
    """Confirm the computed metrics expose every LOCKED metric name (export conformance)."""
    summary = (metrics or {}).get("room_summary", {}) or {}
    parts = (metrics or {}).get("participants", [])
    # A locked metric is satisfied if it appears at the room level OR on participant rows
    # (e.g. speaking_time_share is per-participant).
    available = set(summary.keys())
    for p in parts:
        available |= set(p.keys())
    present = [m for m in locked_metric_names if m in available]
    missing = [m for m in locked_metric_names if m not in available]
    # participant rows must carry the per-participant locked fields
    part_fields = {"participant_id", "turn_count", "speaking_time_share"}
    parts_ok = all(part_fields.issubset(p.keys()) for p in parts) if parts else True
    score = round(len(present) / len(locked_metric_names), 3) if locked_metric_names else 0.0
    return {
        "present": present, "missing": missing,
        "participant_fields_ok": parts_ok,
        "completeness_score": score,
        "passed": not missing and parts_ok,
    }


# ------------------------------------------------------------
# G — Experiment readiness
# ------------------------------------------------------------
def experiment_readiness(
    consistency: Dict[str, Any],
    condition_audit: Dict[str, Any],
    *,
    has_snapshot: bool,
    reproducibility_score: float,
    has_events: bool,
) -> Dict[str, Any]:
    """PASS/FAIL with missing components + integrity + reproducibility scores (0..1)."""
    missing: List[str] = []
    if not has_snapshot:
        missing.append("room_state_snapshot")
    if not has_events:
        missing.append("event_log")
    if not condition_audit.get("passed"):
        missing.append("condition_integrity")
    if not consistency.get("passed"):
        missing.append("data_consistency")

    integrity = float(consistency.get("integrity_score", 0.0))
    repro = float(reproducibility_score)
    status = "PASS" if (
        consistency.get("passed") and condition_audit.get("passed")
        and has_snapshot and has_events and repro >= 0.999
    ) else "FAIL"
    return {
        "status": status,
        "missing_components": missing,
        "data_integrity_score": integrity,
        "reproducibility_score": round(repro, 3),
        "consistency_issues": consistency.get("issues", []),
        "condition_issues": condition_audit.get("issues", []),
    }
