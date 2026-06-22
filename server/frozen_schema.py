from __future__ import annotations

import os

# ============================================================
# 🧊 frozen_schema.py — FEATURE LOCK registry (Final Phase, Priority A)
# ------------------------------------------------------------
# These definitions are FROZEN for the CHI study run. Any future change MUST be a new
# versioned schema (e.g. research_metrics_v3, event_log_v2) — never an in-place edit to
# the locked logic. This module is the single declaration of the locked versions.
# ============================================================

SYSTEM_FROZEN = True
FREEZE_TAG = "chi-study-freeze-1"

# Locked component versions. Bump only by introducing a NEW versioned implementation.
SCHEMA_VERSIONS = {
    "room_state": "v1",            # room_state.py field set
    "research_metrics_v2": "v2",   # research_metrics_v2.py metric definitions (8.5 locked)
    "event_log": "v1",             # event_log table + payload contract
    "room_state_snapshots": "v1",
    "room_metrics_summary": "v1",
    "condition_mapping": "v1",     # event_log.experiment_condition()
    "intervention_types": "v1",    # taxonomy state at freeze (P2 extends via v2)
}

# Canonical experiment conditions (immutable mapping lives in event_log.py).
CONDITIONS = ("no_moderator", "passive_moderator", "active_moderator")

# Event types written to the append-only ground-truth log (event_log.py).
EVENT_TYPES = ("message", "stt", "tts", "intervention", "state_update", "session", "failure")

# Locked metric names that downstream analysis depends on. Do not rename.
# word_gini is the PRIMARY participation-equality measure (Gini on word share) per the
# study design; turn/time variants are secondary.
LOCKED_METRIC_NAMES = (
    "word_gini", "word_entropy", "word_dominance_gap", "word_share", "total_words",
    "turn_count", "speaking_time_share", "avg_turn_duration_ms", "longest_silence_sec",
    "avg_silence_sec", "intervention_count", "interventions_per_minute",
    "turn_gini", "turn_entropy", "dominance_gap", "interruption_estimate",
    "consensus_proxy_final",
)


# ---- P2: strict, deterministic intervention policy (types as logged in code) ----
# Active moderator: trigger condition -> intervention TYPE is deterministic (same input
# state -> same type). The reply TEXT is LLM-generated; the SELECTED TYPE is rule-based.
ACTIVE_INTERVENTION_TYPES = frozenset({
    "active_at_mention", "answered_question", "answered_question_fallback",
    "balance_dominance", "force_turn_balance", "invite_silent",
    "invite_silent_followup", "invite_silent_third", "discussion_drift",
    "progress_summary", "appreciation", "conflict_resolution", "expert_item_hint",
    "item_clarification", "time_warning", "time_warning_1m",
    "high_severity_warning", "language_warning",
})

# Passive moderator: STRICTLY limited to direct mention, final time warning, and safety.
PASSIVE_ALLOWED_INTERVENTIONS = frozenset({
    "passive_at_mention",      # direct user @mention only
    "time_warning_passive",    # final time warning (optional)
    "high_severity_warning",   # safety violation
    "language_warning",        # safety / inappropriate-language
})

# Deterministic trigger -> type map (documentation of the locked selection rules).
ACTIVE_TRIGGER_POLICY = {
    "user @mentions moderator": "active_at_mention",
    "a participant is silent past threshold": "invite_silent",
    "silence persists (2nd window)": "invite_silent_followup",
    "silence persists (3rd window)": "invite_silent_third",
    "one speaker dominates the recent window": "balance_dominance / force_turn_balance",
    "interpersonal conflict cues from 2+ speakers": "conflict_resolution",
    "discussion drifts off the ranking task": "discussion_drift",
    "periodic progress checkpoint": "progress_summary",
    "final minutes remaining": "time_warning / time_warning_1m",
    "inappropriate language / high severity": "language_warning / high_severity_warning",
}

# ---- P3: final analysis-ready dataset entities (export must conform) ----
DATASET_ENTITIES = ("messages", "participants", "groups", "interventions", "metrics_v2", "event_log")


def research_read_only() -> bool:
    """P5 READ-ONLY RESEARCH MODE: when on, runtime config mutations are rejected so
    frozen behavior (metrics/intervention/language logic via settings) can't drift
    mid-study. Toggle with env RESEARCH_READ_ONLY=true."""
    return os.getenv("RESEARCH_READ_ONLY", "false").strip().lower() in ("1", "true", "yes", "on")


def freeze_manifest() -> dict:
    """Return the freeze manifest (embedded in paper bundles + readiness reports)."""
    return {
        "system_frozen": SYSTEM_FROZEN,
        "freeze_tag": FREEZE_TAG,
        "research_read_only": research_read_only(),
        "schema_versions": SCHEMA_VERSIONS,
        "conditions": list(CONDITIONS),
        "event_types": list(EVENT_TYPES),
        "locked_metric_names": list(LOCKED_METRIC_NAMES),
    }
