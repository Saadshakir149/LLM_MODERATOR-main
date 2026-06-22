# 🧊 SYSTEM FREEZE — CHI Study Instrument Lock

**Status:** FROZEN (`freeze_tag = chi-study-freeze-1`). See [`frozen_schema.py`](frozen_schema.py).

This system is a locked experimental instrument. The following are **frozen** and must
not be modified in place:

| Component | Version | Locked location |
|---|---|---|
| `room_state` schema | v1 | `room_state.py` |
| `research_metrics_v2` definitions | v2 | `research_metrics_v2.py` (8.5 `LOCKED DEFINITION` docstrings) |
| `event_log` schema | v1 | `migrations/006_event_log_and_snapshots.sql` |
| intervention types | v1 | taxonomy at freeze |
| condition mapping | v1 | `event_log.experiment_condition()` |

## The one rule

> **Any future change MUST be a new versioned schema (v3, v4 …), never an edit to the
> locked logic.**

Concretely:
- New metric definition → add `research_metrics_v3.py`; do not change v2 formulas.
- New event payload → add a new `event_type` or `event_log_v2`; do not repurpose fields.
- New intervention taxonomy (P2) → version it; do not redefine existing labels.
- Migrations are append-only and numbered (`007_…`, `008_…`).

## Why frozen logic matters

Changing a metric definition mid-study makes sessions collected before and after **not
comparable**, silently invalidating cross-condition analysis. Versioning preserves the
ability to recompute every past session under its original definition.

## Locked metric definitions (8.5)

- **`turn_count`** — a turn is a maximal run of consecutive messages by the same student.
- **`speaking_time_share`** — derived ONLY from `voice_recordings.duration_ms`; never from
  text length, message counts, or timestamps. Absent durations ⇒ shares are 0 and
  `durations_available = false` (never back-filled).
- **`consensus_proxy`** — a lexical PROXY. Always reported as `consensus_proxy`; never
  claimed as a ground-truth consensus measure. Validated consensus comes from the P4
  summary pipeline.

## Reproducibility guarantee

The only non-deterministic step is the upstream LLM normalization at STT time. Its output
is **frozen as durable data** (`voice_recordings.transcript_text` = raw, `messages.message`
= normalized). All downstream analysis (room_state, metrics, validators, exports) is
deterministic and recomputable from the database alone — verified by
`tests/test_reproducibility.py` (byte-identical output across runs).
