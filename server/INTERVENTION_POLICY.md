# 🧭 Moderator Intervention Policy (FROZEN — P2)

Canonical source: [`frozen_schema.py`](frozen_schema.py) (`ACTIVE_TRIGGER_POLICY`,
`ACTIVE_INTERVENTION_TYPES`, `PASSIVE_ALLOWED_INTERVENTIONS`). Enforced by
`validation.audit_passive_constraints`.

## Determinism guarantee
The **selection of an intervention TYPE is deterministic**: the same triggering state
produces the same intervention type (rule-based, in the monitor loop). The reply **TEXT**
is LLM-generated and is *not* claimed to be deterministic — only the type selection and
the trigger→type mapping are frozen. Reply text is stored verbatim, so analysis of *which*
intervention fired (the type) is fully reproducible.

## Active moderator — trigger → type (deterministic)

| Trigger condition | Intervention type |
|---|---|
| User @mentions the moderator | `active_at_mention` |
| Participant silent past threshold | `invite_silent` |
| Silence persists (2nd / 3rd window) | `invite_silent_followup` / `invite_silent_third` |
| One speaker dominates recent window | `balance_dominance` / `force_turn_balance` |
| Interpersonal conflict cues from 2+ speakers | `conflict_resolution` |
| Discussion drifts off the ranking task | `discussion_drift` |
| Periodic progress checkpoint | `progress_summary` |
| Final minutes remaining | `time_warning` / `time_warning_1m` |
| Inappropriate language / high severity | `language_warning` / `high_severity_warning` |

## Passive moderator — STRICTLY limited
A passive session may emit **only** these intervention types — no exceptions:

- `passive_at_mention` — direct user @mention only
- `time_warning_passive` — final time warning (optional)
- `high_severity_warning`, `language_warning` — safety violation only

Any other intervention type logged in a passive session is a **constraint violation** and
is rejected by `audit_passive_constraints` (surfaced in the final readiness check).

## No-moderator condition
No interventions are emitted; no monitor runs. (Condition mapping is ready; wiring the
mode into room creation is tracked separately and is not part of this freeze.)
