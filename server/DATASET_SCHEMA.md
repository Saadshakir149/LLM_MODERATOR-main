# 📦 Final Analysis-Ready Dataset Schema (FROZEN — P3)

Six entities. Exports (`paper_bundle`, metrics export) conform to this structure.
Canonical entity list: `frozen_schema.DATASET_ENTITIES`.

## 1. messages
`id, room_id, username, message, message_type, created_at, metadata(JSON: input_mode,
word_count, language, …)`. `message` = final shown text; raw STT lives in `voice_recordings`.

## 2. participants
`id, room_id, username, display_name, joined_at`.

## 3. groups
A **group = a room** (a 3-person triad + moderator). Key: `rooms.id`. Carries the
immutable `mode` → experiment condition.

## 4. interventions  (`moderator_interventions`)
`id, room_id, intervention_type, target_user, timestamp`. Types per
[INTERVENTION_POLICY.md](INTERVENTION_POLICY.md).

## 5. metrics_v2
Per-participant rows: `participant_id, message_count, turn_count, turn_share,
speaking_time_ms, speaking_time_share, avg_turn_duration_ms`.
Room summary: locked metric names in `frozen_schema.LOCKED_METRIC_NAMES`.
Persisted to `research_metrics_v2` (tidy) + `room_metrics_summary` (wide).

## 6. event_log
`event_id, room_id, session_id, experiment_condition, event_type
(message|stt|tts|intervention|state_update|session|failure), payload_json, timestamp`.
The append-only ground truth.

## Conformance
`validation.check_schema_completeness` verifies the computed metrics expose every locked
metric name + required per-participant fields. Reported in
`/admin/research/experiment_readiness_final/<room_id>`.
