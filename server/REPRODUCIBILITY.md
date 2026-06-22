# 🔁 Reproducibility Statement (FROZEN — P5)

## Guarantee
> Given the **same `event_log` / stored messages** and the **same (frozen) metrics
> pipeline**, the system produces **identical** analysis outputs on every run.

This holds because all analysis (`research_metrics_v2`, `room_state` derivation,
validators, exports) is **pure and deterministic** over durable database data, with **no
runtime-memory dependency**. Verified by `tests/test_reproducibility.py`, which computes
the full pipeline twice on a scripted session and asserts **byte-identical** JSON, and the
live `reproducibility_score` (recompute-and-compare) in the readiness endpoints.

## Scope / boundary
The only non-deterministic step is the upstream **LLM normalization** at STT time. Its
output is **frozen as durable data** — `voice_recordings.transcript_text` (raw STT) and
`messages.message` (normalized) — so it is captured once and never recomputed. Every
downstream research definition operates on this frozen data and is therefore reproducible.
LLM reply **text** for interventions is likewise stored verbatim; only intervention **type
selection** is claimed deterministic (see INTERVENTION_POLICY.md).

## No runtime logic affects research definitions
`room_state` is operational only; the authoritative metrics never read it. Config that
could alter behavior (e.g. silence thresholds) is frozen under READ-ONLY RESEARCH MODE
(`RESEARCH_READ_ONLY=true`), which rejects settings mutations mid-study.

## ⚠️ Open definition to confirm before locking (P4)
The pre-registration text states **"Gini = word-share inequality."** The **frozen
implementation computes Gini on TURN shares** (`turn_gini`) and message-count shares — NOT
word-count shares. These are different measures. This was **not changed silently**: per the
freeze rule, the PI must either
1. accept the implemented **turn-share Gini** as the locked definition (and update the
   prereg wording), **or**
2. authorize a **version bump (v3)** to add a word-share Gini metric.
Until resolved, `consensus_proxy` and `Gini` definitions stand as implemented and labeled.
