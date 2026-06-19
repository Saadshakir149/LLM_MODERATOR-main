"""Priority B — End-to-end reproducibility + validation test.

Builds a scripted P1/P2/P3 session (messages, interventions, silence, language
switching, voice durations) and asserts:

  * Running the full DETERMINISTIC analysis pipeline twice on identical input yields
    byte-identical output (JSON-equal)  -> reproducibility for research validity.
  * The authoritative metric turn_count == an INDEPENDENT event-derived turn count.
  * The data-consistency + condition validators behave correctly.

NOTE on scope: the only non-deterministic step in the live system is the upstream LLM
normalization. Its output is FROZEN as durable data (raw_text + normalized stored), so
re-analysis from stored messages is fully deterministic — which is what this test
verifies. No LLM/STT/TTS is invoked here.

Run:  python tests/test_reproducibility.py   (from server/)
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import research_metrics_v2 as RM2   # noqa: E402
import validation as V              # noqa: E402

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  [PASS] {name}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}")


BASE = 1718000000


def at(sec):
    return datetime.fromtimestamp(BASE + sec, tz=timezone.utc).isoformat()


def build_session():
    """Deterministic scripted session (fixed timestamps + ids)."""
    msgs = [
        {"id": "m1", "username": "P1", "message": "water pehle rakho", "created_at": at(0),
         "metadata": {"input_mode": "voice"}},
        {"id": "m2", "username": "P1", "message": "haan theek hai", "created_at": at(8),
         "metadata": {"input_mode": "voice"}},
        {"id": "m3", "username": "P2", "message": "I agree, water first", "created_at": at(20),
         "metadata": {"input_mode": "voice"}},
        # ~90s silence gap here (20 -> 110)
        {"id": "m4", "username": "P3", "message": "compass bhi zaroori hai", "created_at": at(110),
         "metadata": {"input_mode": "voice"}},
        {"id": "m5", "username": "P1", "message": "sahi baat hai, agree", "created_at": at(125),
         "metadata": {"input_mode": "voice"}},
        {"id": "m6", "username": "Moderator", "message": "P3, what do you think?",
         "created_at": at(95), "message_type": "moderator"},
    ]
    interventions = [
        {"intervention_type": "participation_balance", "target_user": "P3", "timestamp": at(95)},
    ]
    durations = {"m1": 4000, "m2": 3000, "m3": 5000, "m4": 6000, "m5": 3500}
    voice_recordings = [{"message_id": k, "duration_ms": v} for k, v in durations.items()]
    return msgs, interventions, durations, voice_recordings


def run_pipeline():
    msgs, interventions, durations, _ = build_session()
    return RM2.compute_all(
        "sim-room", msgs,
        interventions=interventions,
        durations=durations,
        students=["P1", "P2", "P3"],
        condition="active_moderator",
        session_started_at=at(0),
        session_ended_at=at(130),
    )


print("\n[B1] Determinism — identical input -> identical output across runs")
r1 = run_pipeline()
r2 = run_pipeline()
j1 = json.dumps(r1, sort_keys=True)
j2 = json.dumps(r2, sort_keys=True)
check("two runs produce byte-identical JSON", j1 == j2)
# A third run after touching unrelated state must still match.
_ = RM2.compute_all("other", [], students=[])
check("third run still identical", json.dumps(run_pipeline(), sort_keys=True) == j1)

print("\n[B2] Cross-check — metric turn_count == independent event-derived count")
msgs, interventions, durations, voice_recordings = build_session()
derived = V.derive_turn_count(msgs)
metric_turns = r1["room_summary"]["turn_count"]
# Speaker runs (students only): P1,P1 | P2 | P3 | P1  -> 4 turns
check("derived turn count == 4", derived == 4)
check("metric turn_count == derived", metric_turns == derived)

print("\n[C] Consistency validator")
cons = V.check_consistency(msgs, interventions, voice_recordings, events=[], metrics=r1)
check("turn_count_matches True", cons["checks"]["turn_count_matches"] is True)
check("all_timestamps_present True", cons["checks"]["all_timestamps_present"] is True)
check("voice_one_to_one True", cons["checks"]["voice_one_to_one"] is True)
check("flags empty event_log", any("event_log empty" in i for i in cons["issues"]))

print("\n[C2] Consistency catches a broken voice mapping")
bad_vr = voice_recordings[:-1] + [{"message_id": "ghost", "duration_ms": 1000}]
cons_bad = V.check_consistency(msgs, interventions, bad_vr, events=[], metrics=r1)
check("voice_one_to_one False on mismatch", cons_bad["checks"]["voice_one_to_one"] is False)

print("\n[D] Condition audit")
room = {"id": "sim-room", "mode": "active"}
snaps = [{"experiment_condition": "active_moderator"}]
aud = V.audit_condition(room, "active_moderator", r1, snaps)
check("condition audit passes", aud["passed"] is True)
check("no drift detected", aud["condition_drift_detected"] is False)
drift = V.audit_condition(room, "active_moderator", r1, [{"experiment_condition": "passive_moderator"}])
check("drift detected when snapshot disagrees", drift["condition_drift_detected"] is True)

print("\n[E] Failure report from events")
events = [
    {"event_type": "failure", "timestamp": at(5), "payload_json": {"kind": "stt", "error": "x"}},
    {"event_type": "failure", "timestamp": at(6),
     "payload_json": {"kind": "tts_provider_fallback", "recovery": "used openai"}},
    {"event_type": "message", "timestamp": at(0), "payload_json": {"message_id": "m1"}},
]
fr = V.build_failure_report(events, room_id="sim-room")
check("1 stt failure captured", len(fr["stt_failures"]) == 1)
check("1 fallback captured", len(fr["llm_fallbacks"]) == 1)
check("recovery action recorded", len(fr["recovery_actions"]) == 1)
check("total_failures == 2", fr["total_failures"] == 2)

print("\n[G] Readiness scoring")
ready = V.experiment_readiness(cons, aud, has_snapshot=True, reproducibility_score=1.0, has_events=False)
check("FAIL when event_log missing", ready["status"] == "FAIL")
check("event_log listed missing", "event_log" in ready["missing_components"])
cons_full = dict(cons); cons_full["passed"] = True; cons_full["issues"] = []
ready2 = V.experiment_readiness(cons_full, aud, has_snapshot=True, reproducibility_score=1.0, has_events=True)
check("PASS when all green + repro 1.0", ready2["status"] == "PASS")

print("\n[P3] Finalization guarantee — never silently succeed")
all_ok = {k: True for k in V.FINALIZATION_STEPS}
check("all steps -> COMPLETE", V.assess_finalization(all_ok)["status"] == "COMPLETE")
no_snap = dict(all_ok); no_snap["snapshot_exists"] = False
verdict = V.assess_finalization(no_snap)
check("missing snapshot -> INCOMPLETE", verdict["status"] == "INCOMPLETE")
check("missing step listed", "snapshot_exists" in verdict["missing_steps"])
check("empty steps -> INCOMPLETE", V.assess_finalization({})["status"] == "INCOMPLETE")

print("\n[P2] Passive constraint audit")
import frozen_schema as FS  # noqa: E402
allowed = set(FS.PASSIVE_ALLOWED_INTERVENTIONS)
ok_iv = [{"intervention_type": "passive_at_mention"}, {"intervention_type": "time_warning_passive"}]
bad_iv = ok_iv + [{"intervention_type": "balance_dominance"}]
check("passive ok -> passed", V.audit_passive_constraints("passive_moderator", ok_iv, allowed)["passed"])
ap_bad = V.audit_passive_constraints("passive_moderator", bad_iv, allowed)
check("passive violation caught", ap_bad["passed"] is False and "balance_dominance" in ap_bad["violations"])
check("active not subject to passive rule", V.audit_passive_constraints("active_moderator", bad_iv, allowed)["applicable"] is False)

print("\n[P3] Schema completeness")
sc = V.check_schema_completeness(r1, FS.LOCKED_METRIC_NAMES)
check("all locked metrics present", sc["passed"] is True)
check("completeness score 1.0", sc["completeness_score"] == 1.0)
sc_bad = V.check_schema_completeness({"room_summary": {"turn_count": 5}}, FS.LOCKED_METRIC_NAMES)
check("missing metrics flagged", sc_bad["passed"] is False and len(sc_bad["missing"]) > 0)

print("\n[P1] Pre-registration lock")
import preregistration as PR  # noqa: E402
ver = PR.verify()
check("prereg present", ver["present"] is True)
check("current hash computed", isinstance(ver["current_hash"], str) and len(ver["current_hash"]) == 64)

print(f"\n==== {_PASS} passed, {_FAIL} failed ====")
sys.exit(1 if _FAIL else 0)
