# ✅ End-to-End Dry Run — Pre-Supervisor Checklist

Run this verbatim once. Every step lists the **expected** result; if any differs, stop and note it.
Admin endpoints need the header `X-Admin-Token: <ADMIN_TOKEN>` (your `.env`).

---

## 0. Config preconditions (`server/.env`)
- [ ] `LLM_PROVIDER=openai`  (Groq key removed) + `OPENAI_CHAT_MODEL=gpt-4o-mini`
- [ ] `OPENAI_API_KEY` set (no leading space)
- [ ] `UPLIFT_API_KEY` set, `UPLIFT_VOICE_ID_URDU=v_8eelc901`
- [ ] `ADMIN_TOKEN` set (for the admin endpoints below)
- [ ] `FRONTEND_URL=http://localhost:3000`

## 1. Database migrated
Run in Supabase SQL editor (idempotent), then **Settings → API → Reload schema cache**:
```sql
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS primary_language TEXT DEFAULT 'en';
SELECT table_name FROM information_schema.tables WHERE table_name IN
('voice_recordings','event_log','room_state_snapshots','research_metrics_v2','room_metrics_summary');
-- expect 5 rows
```
- [ ] 5 tables present + `rooms.primary_language` exists

## 2. Start server → preflight passes
```
cd server && python app.py
```
- [ ] Log shows **`✅ Preflight: all required tables present (DB migrated)`**
- [ ] `✅ TTS voice provider initialized: openai`
- [ ] No `PGRST205` / `event_log write failed` errors

Confirm via API:
```
curl -s -H "X-Admin-Token: $ADMIN_TOKEN" http://localhost:5000/admin/research/preflight
```
- [ ] Returns `{"ok": true, "missing": []}`

## 3. Start frontend
```
cd client/frontend && npm start
```
- [ ] Loads at http://localhost:3000

## 4. Join an Urdu room (×3 participants)
Open **3 browser tabs** → `http://localhost:3000/join/active` in each.
- [ ] Each shows the **language selector** → click **Roman Urdu** → **Join Active Session**
- [ ] All 3 land in the same `/chat/<room_id>?...&language=roman_urdu`  ← note the **room_id**
- [ ] Task intro card appears **in Roman Urdu** and is **read aloud** in Roman Urdu (Uplift voice)

## 5. Speak (STT + language + storage)
In one tab, **hold the mic**, say an Urdu sentence (e.g. *"mujhe lagta hai paani sab se zaroori hai"*), release.
- [ ] Transcript appears as a **🎤 Voice** message in **Roman Urdu (Latin script)** — no Urdu/foreign script
- [ ] Server log: `✅ STT result (roman_urdu …)` and `✅ Staged audio …`
- [ ] ▶ on the message **plays back** your recording

## 6. Moderator responds — right language + voiced
Type or say **"moderator, aap ka kya khayal hai"** (note: no `@` needed).
- [ ] Moderator **replies in Roman Urdu**, stays in Roman Urdu across turns (no flip-flop)
- [ ] Reply is **spoken aloud**; server log: `✅ TTS generated (roman_urdu)` (no Uplift-fallback warning = real Urdu voice)
- [ ] No `Possible fake name` discards in the log

## 7. End the session → COMPLETE
Click **End & Evaluate** in one tab.
- [ ] Server log: **`🧊 Session finalized … finalization: COMPLETE`**
- [ ] No `INCOMPLETE` / `finalize_error`

## 8. Verify the research artifact (use the room_id from step 4)
```
TOKEN=$ADMIN_TOKEN ; RID=<room_id>
curl -s -H "X-Admin-Token: $TOKEN" "http://localhost:5000/admin/research/session/$RID/validate"
curl -s -H "X-Admin-Token: $TOKEN" "http://localhost:5000/admin/research/metrics/$RID/v2"
curl -s -H "X-Admin-Token: $TOKEN" "http://localhost:5000/admin/research/experiment_readiness_final/$RID"
curl -s -H "X-Admin-Token: $TOKEN" "http://localhost:5000/admin/export/paper_bundle/$RID" -o paper_bundle.zip
```
- [ ] `/validate` → `consistency.passed: true`, `reproducibility_score: 1.0`, `condition_audit.passed: true`
- [ ] `/metrics/.../v2` → `room_summary.word_gini` present; one row per participant with `word_share`
- [ ] `experiment_readiness_final` → `dataset_integrity_score` + `reproducibility_score` (note: returns **NOT READY** until the preregistration is **locked** — expected)
- [ ] `paper_bundle.zip` downloads and contains: `event_log.csv, metrics_v2.json, room_state_snapshot.json, intervention_log.csv, timeline.json, failure_report.json, session_metadata.json`

## 9. Spot-check the DB (Supabase)
```sql
SELECT event_type, count(*) FROM event_log WHERE room_id='<room_id>' GROUP BY event_type;  -- message/stt/tts/intervention/session
SELECT count(*) FROM voice_recordings WHERE room_id='<room_id>';                            -- = #voice messages
SELECT condition, gini, turn_count, intervention_count FROM room_metrics_summary WHERE room_id='<room_id>';
```
- [ ] event_log has rows; voice_recordings 1:1 with voice messages; summary row has `condition` + `gini`

---

## Repeat for the Passive + English arms
- [ ] `/join/passive` → **Roman Urdu** → moderator stays quiet unless you say "moderator", final-time reminder only
- [ ] `/join/active` → **English** → everything in English, spoken via OpenAI voice

## What to show the supervisor
1. **Reproducible** — `reproducibility_score = 1.0`, reconstructable from DB only.
2. **Objective metrics** — word-share Gini (primary), dominance, silence, intervention frequency by type, time-to-consensus.
3. **Clean condition labelling** — `condition_audit.passed`, condition on every summary/snapshot.
4. **No silent data loss** — finalization = COMPLETE, failures in `failure_report.json`.
5. **One-click artifact** — the paper bundle ZIP.

## Known "expected NOT READY" until you finalize
`experiment_readiness_final` stays **NOT READY** until: preregistration is **locked** (set the min-message exclusion threshold + final item list, then `preregistration.lock()`). Everything else should be green.
