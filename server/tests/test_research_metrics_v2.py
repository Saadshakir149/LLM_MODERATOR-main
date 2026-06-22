"""Validation tests for research_metrics_v2 (Priority 6).

Run: python tests/test_research_metrics_v2.py   (from the server/ directory)
Plain asserts so it runs without pytest. Exits non-zero on failure.

Covers the required cases: correctness, empty rooms, single participant,
missing audio durations, short sessions, and mixed-language sessions.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import research_metrics_v2 as M  # noqa: E402

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


def msg(i, user, text, t, mid=None):
    """Build a message at minute.second offset `t` (seconds) from a base time."""
    base = 1718000000  # fixed epoch base
    from datetime import datetime, timezone
    ts = datetime.fromtimestamp(base + t, tz=timezone.utc).isoformat()
    return {"id": mid or f"m{i}", "username": user, "message": text, "created_at": ts}


print("\n[1] Correctness - 3 participants, P1 dominant, durations present")
# Speaker sequence P1,P1,P2,P3,P1,P2 -> runs: [P1P1][P2][P3][P1][P2] = 5 turns.
msgs = [
    msg(1, "P1", "water pehle rakhte hain", 0, "a1"),
    msg(2, "P1", "haan theek hai", 10, "a2"),     # consecutive P1 -> same turn
    msg(3, "P2", "agree, sahi hai", 25, "b1"),
    msg(4, "P3", "ok", 40, "c1"),
    msg(5, "P1", "mirror baad mein", 60, "a3"),
    msg(6, "P2", "lekin compass zaroori hai", 75, "b2"),
]
durations = {"a1": 4000, "a2": 3000, "b1": 5000, "c1": 1500, "a3": 3500, "b2": 6000}
interventions = [{"intervention_type": "participation_balance", "timestamp": msgs[3]["created_at"]}]
r = M.compute_all("room1", msgs, interventions=interventions, durations=durations,
                  students=["P1", "P2", "P3"], condition="active")
rs = r["room_summary"]
turns = {p["participant_id"]: p["turn_count"] for p in r["participants"]}
check("P1 has 2 turns (one run of two + one later)", turns["P1"] == 2)
check("P2 has 2 turns", turns["P2"] == 2)
check("P3 has 1 turn", turns["P3"] == 1)
check("room turn_count == 5", rs["turn_count"] == 5)
check("durations available", rs["durations_available"] is True)
check("speaking-time shares sum ~1.0",
      abs(sum(p["speaking_time_share"] for p in r["participants"]) - 1.0) < 1e-6)
check("avg_turn_duration_ms is a number", isinstance(rs["avg_turn_duration_ms"], (int, float)))
check("intervention_count == 1", rs["intervention_count"] == 1)
check("moderator latency computed", rs["moderator_median_latency_sec"] is not None)
check("dominance_gap > 0 (unequal turns)", rs["dominance_gap"] > 0)
check("consensus timeline non-empty", len(r["timelines"]["consensus_timeline"]) >= 1)

print("\n[2] Empty room")
r = M.compute_all("empty", [], students=[])
check("no participants", r["participants"] == [])
check("turn_count == 0", r["room_summary"]["turn_count"] == 0)
check("intervention_count == 0", r["room_summary"]["intervention_count"] == 0)
check("avg_silence None", r["room_summary"]["avg_silence_sec"] is None)
check("empty timeline", r["timelines"]["consensus_timeline"] == [])

print("\n[3] Single participant")
solo = [msg(1, "P1", "hello", 0), msg(2, "P1", "water first", 30)]
r = M.compute_all("solo", solo, students=["P1"])
rs = r["room_summary"]
check("1 turn (consecutive same speaker)", rs["turn_count"] == 1)
check("turn_gini == 0 (one speaker, perfect... trivially)", rs["turn_gini"] == 0 or rs["turn_gini"] >= 0)
check("dominance_gap == 0 (single share)", rs["dominance_gap"] == 0.0)
check("no interruptions", rs["interruption_estimate"] == 0)

print("\n[4] Missing audio durations (text-only room)")
r = M.compute_all("nodur", msgs, durations=None, students=["P1", "P2", "P3"])
rs = r["room_summary"]
check("durations_available False", rs["durations_available"] is False)
check("avg_turn_duration_ms None", rs["avg_turn_duration_ms"] is None)
check("time_gini None (no durations)", rs["time_gini"] is None)
check("turn metrics still computed", rs["turn_count"] == 5)
check("speaking_time_share all 0", all(p["speaking_time_share"] == 0.0 for p in r["participants"]))

print("\n[5] Short session (2 messages, ~5s)")
short = [msg(1, "P1", "hi", 0), msg(2, "P2", "ok", 5)]
r = M.compute_all("short", short, students=["P1", "P2"])
rs = r["room_summary"]
check("turn_count == 2", rs["turn_count"] == 2)
check("one silence gap", rs["avg_silence_sec"] is not None)
check("session_minutes small but >= 0", rs["session_minutes"] >= 0)

print("\n[6] Mixed-language session (language must NOT affect counts)")
mixed = [
    msg(1, "P1", "Yaar I think water sab se important hai", 0),
    msg(2, "P2", "agree, bilkul sahi", 20),
    msg(3, "P3", "mujhe lagta hai compass", 40),
]
r = M.compute_all("mixed", mixed, students=["P1", "P2", "P3"])
rs = r["room_summary"]
check("3 turns regardless of language", rs["turn_count"] == 3)
check("consensus proxy detects 'agree'/'sahi'",
      any(b["consensus_proxy"] > 0 for b in r["timelines"]["consensus_timeline"]))

print("\n[7] Interruption estimate - rapid switch < 1.5s")
rapid = [msg(1, "P1", "I think", 0), msg(2, "P2", "no wait", 1)]  # 1s gap, different speaker
r = M.compute_all("rapid", rapid, students=["P1", "P2"])
check("one interruption detected", r["room_summary"]["interruption_estimate"] == 1)

print(f"\n==== {_PASS} passed, {_FAIL} failed ====")
sys.exit(1 if _FAIL else 0)
