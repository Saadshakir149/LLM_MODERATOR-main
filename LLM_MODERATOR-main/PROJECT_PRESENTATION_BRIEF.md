# LLM Moderator — Project Presentation Brief

> A ready-to-use brief for generating a PowerPoint. Each "SLIDE" block can become one slide.

---

## SLIDE 1 — Title
**LLM Moderator: An AI-Moderated Collaborative Learning & Group-Discussion Research Platform**
Subtitle: *Studying how an LLM moderator shapes participation, conflict, and consensus in small-group problem solving (the "Desert Survival" task).*

---

## SLIDE 2 — One-Line Summary / Elevator Pitch
A real-time web platform where small groups (3 students) solve a survival ranking task in a chat room, while an **AI moderator (LLM)** facilitates the discussion. The system records every interaction and computes **research metrics** to compare an **Active** moderator vs. a **Passive** moderator.

---

## SLIDE 3 — The Problem / Motivation
- Online group discussions often suffer from **unequal participation** (one person dominates, others stay silent), **unresolved conflict**, and **going off-task**.
- Human facilitators don't scale.
- **Research question:** Can an LLM act as an effective discussion moderator — increasing fairness, de-escalating conflict, keeping groups on task, and improving outcomes?

---

## SLIDE 4 — What the System Does
1. Auto-groups students into rooms of 3.
2. Presents a **Desert Survival** scenario: rank 12 salvaged items by survival importance.
3. An **AI moderator** facilitates in real time — invites quiet members, balances dominant speakers, de-escalates conflict, refocuses off-task chat, gives time warnings, and summarizes.
4. Runs a fixed **15-minute** session, then auto-extracts a group ranking.
5. Generates **personalized feedback** per student.
6. Logs everything to a database and computes **research metrics**.

---

## SLIDE 5 — The Task: Desert Survival
- Classic group decision-making exercise (used widely in psychology/teamwork research).
- Group must rank **12 items** from 1 (most important) to 12 (least important) for survival.
- **Three interchangeable scenarios** (chosen randomly per room):
  1. **Plane Crash Survival** (Arizona desert, 110°F)
  2. **Lost Hikers in the Desert**
  3. **Broken Down Vehicle in the Desert**
- Each scenario has an **expert ("correct") ranking** — used to score the group's answer (ranking accuracy).
- Example items: cosmetic mirror, water, flashlight, parachute, hunting knife, plastic sheet, matches, compass, map, salt tablets, survival book.

---

## SLIDE 6 — Two Experimental Conditions (Core of the Study)
| | **Active Moderator** | **Passive Moderator** |
|---|---|---|
| Role | Proactively facilitates | Minimal intervention |
| Quiet members | Invites them by name | Rarely |
| Dominance | Rebalances toward others | No |
| Conflict | De-escalates | No |
| Off-task | Refocuses on the task | No |
| Purpose | Treatment group | Control / baseline |

This A/B comparison is what the research measures.

---

## SLIDE 7 — Research Questions (RQ1–RQ5)
- **RQ1 — Participation equality:** Does active moderation make speaking shares more equal? (Gini coefficient, Shannon entropy, dominance gap)
- **RQ2 — Conflict & repair:** Does it reduce conflict and increase "repairs" (reconciliation)? (conflict count, repair rate, time-to-repair)
- **RQ3 — Dominance:** Does it reduce single-speaker dominance?
- **RQ4 — On-task focus:** Does it keep discussion task-relevant?
- **RQ5 — Responsiveness:** How quickly do students respond after a moderator intervention? (intervention follow-up latency)

---

## SLIDE 8 — System Architecture (High Level)
```
React Frontend  ◄──Socket.IO/WebSocket──►  Flask Backend  ◄──HTTPS──►  Supabase (PostgreSQL)
  (Port 3000)                                (Port 5000)                  (rooms, messages, metrics)
                                                  │
                                                  ▼
                                       LLM Provider (Groq / OpenAI)
                                       Llama-3.1-8b-instant or GPT-4o-mini
```
- **Frontend:** React 18 SPA, real-time chat UI.
- **Backend:** Python Flask + Flask-SocketIO, event-driven.
- **Database:** Supabase (hosted PostgreSQL) — full persistence + research tables.
- **AI:** Pluggable LLM — **Groq (Llama-3.1-8b-instant)** as primary/fallback, **OpenAI (GPT-4o-mini)** optional.

---

## SLIDE 9 — Technology Stack
**Frontend:** React 18, React Router, Socket.IO-client, Tailwind CSS, Framer Motion, React-Markdown
**Backend:** Python 3.12, Flask, Flask-SocketIO, Flask-CORS, threading async mode
**AI / LLM:** Groq SDK (Llama 3.1), OpenAI (GPT-4o-mini), LangChain-style prompt management
**Database:** Supabase / PostgreSQL (UUIDs, JSONB, triggers, indexes)
**Audio (optional):** Text-to-Speech & Speech-to-Text via OpenAI audio + pydub/FFmpeg
**Deployment:** Vercel (frontend), Render (backend) — `render.yaml`, `vercel.json` included

---

## SLIDE 10 — Real-Time Communication (Socket.IO Events)
- `connect` / `disconnect` — connection lifecycle
- `create_room` — host starts a session
- `join_room` — student joins; chat history replayed
- `send_message` — student message → broadcast → may trigger AI
- `submit_ranking` — group submits final item ranking
- `end_session` — wrap up + feedback
- Server emits: `receive_message`, `chat_history`, `participants_update`, etc.

---

## SLIDE 11 — How the AI Moderator Decides to Act (Active Mode Logic)
The moderator does **not** reply to every message. It picks an **intervention type** based on the discussion state:
- `answer_question` — a student directly @mentioned/asked the moderator
- `invite_silent` — someone idle ≥ **90s** (then nudges at 180s, 270s)
- `balance_dominance` — one person > **50%** of recent messages → redirect to others
- `time_warning` — near the 15-minute limit
- `summarize` — periodic progress recap
- `appreciate` — reinforce good contributions
- De-escalation when interpersonal conflict is detected from 2+ speakers

Each type uses a tailored prompt and temperature for natural, targeted replies.

---

## SLIDE 12 — Research Metrics Computed (the "Science")
**Participation equality**
- **Gini coefficient** (0 = perfectly equal, 1 = one person dominates)
- **Shannon entropy** (normalized 0–1 evenness of speaking shares)
- **Dominance gap** (max share − min share)

**Conflict dynamics**
- Conflict-keyword detection, **repair detection**, **repair rate**, mean time-to-repair

**Task & responsiveness**
- **Ranking accuracy** vs. expert ranking
- **Time to consensus**, turn-taking, response times
- **Intervention follow-up latency** (RQ5)

---

## SLIDE 13 — Database Schema (Supabase / PostgreSQL)
**Core tables**
- `rooms` — mode (active/passive), status, participant count, scenario, progress
- `participants` — anonymous display names, socket IDs, activity timestamps
- `messages` — every chat/system/story/moderator/task message (+ JSONB metadata)
- `sessions` — completed session records (duration, counts)

**Research tables (migration 003)**
- `research_metrics` — Gini, entropy, dominance, conflict/repair, ranking accuracy per room
- `participant_metrics` — per-student message/word counts, share of talk
- `moderator_interventions` — every intervention (type, target, timestamp)
- `conflict_episodes` — conflict→repair pairs with severity & time-to-repair

Features: UUID keys, **auto-update triggers** (participant counts, activity, message counts), GIN indexes on JSONB.

---

## SLIDE 14 — Session Lifecycle (Flow)
1. Student opens app → auto-joins an Active or Passive room.
2. Room fills to **3 participants** → scenario randomly assigned → session starts.
3. **15-minute research clock** begins; task intro shown.
4. Students discuss & rank; moderator intervenes per its logic (Active) or stays quiet (Passive).
5. Milestone time warnings (e.g., 6 / 3 min left).
6. At time-up: group ranking auto-extracted from chat → scored against expert ranking.
7. Metrics computed & stored; **personalized feedback** generated per student.
8. Session marked completed in DB.

---

## SLIDE 15 — Admin Dashboard & Data Export
A built-in admin panel (`/admin` API + React `AdminDashboard`) provides:
- Live room & participant monitoring, system stats
- Create / end / delete rooms, change status
- Runtime configuration (LLM provider, model, timing thresholds) stored in DB
- View server logs
- **Research data export** — per-room metrics, chat transcripts (CSV/JSON), study-wide summary
- Endpoints: `/admin/rooms`, `/admin/stats`, `/admin/settings`, `/admin/research/export`, `/admin/research/summary`, `/admin/research/metrics/<room_id>`

---

## SLIDE 16 — Key Engineering Features
- **Provider-agnostic LLM layer** with automatic Groq fallback if OpenAI key missing.
- **Robust intervention timing** via background threads (silence monitor, 15-min chain).
- **Content safety** — inappropriate-language detection & severity checks.
- **Anonymous participation** — no accounts, auto-generated names (privacy-friendly for research ethics).
- **Resilient logging** — server-wide + per-room logs; UTF-8 emoji-safe on Windows.
- **Reconnection handling** — chat history replay on rejoin.

---

## SLIDE 17 — Privacy & Research Ethics
- No personal accounts; participants get auto-names ("Student_1234").
- API keys stay server-side only; never exposed to the browser.
- All conversations stored for analysis in anonymized form (informed consent assumed).
- Row-Level Security intentionally disabled for the research DB (server-trusted).

---

## SLIDE 18 — Results / What Can Be Measured (for Demo or Findings)
- Compare **Active vs. Passive** rooms on: Gini, entropy, dominance gap, conflict/repair rate, ranking accuracy, response latency.
- Hypothesis: Active moderation → **lower Gini (more equal), higher repair rate, higher on-task ratio, better ranking accuracy.**
- *(Plug in your actual numbers from `/admin/research/summary`.)*

---

## SLIDE 19 — Challenges & Solutions
| Challenge | Solution |
|---|---|
| When should the AI intervene without spamming? | State-based intervention selection + per-person cooldowns |
| Python 3.12 broke eventlet | Auto-switch Socket.IO to threading mode |
| OpenAI cost/availability | Groq Llama-3.1 fallback, provider-agnostic layer |
| Measuring "fairness" objectively | Gini + entropy + dominance metrics |
| Extracting a final ranking from free chat | Auto-parse ranking from conversation at session end |

---

## SLIDE 20 — Future Work
- Horizontal scaling (Redis Socket.IO adapter, load balancing).
- Larger / configurable group sizes and more task types (dataset-agnostic).
- Statistical analysis pipeline + dashboards for study results.
- Fine-tuned or specialized moderator models.
- Voice-first sessions (TTS/STT already scaffolded).

---

## SLIDE 21 — Conclusion
The LLM Moderator demonstrates that a large language model can serve as a **real-time, scalable discussion facilitator** for small-group collaborative tasks — and provides a full **research instrument** (task + metrics + data export) to rigorously evaluate its impact on participation equality, conflict resolution, and task performance.

---

## APPENDIX — Quick Facts for Q&A
- **Group size:** 3 students per room
- **Session length:** 15 minutes (fixed research block)
- **Silence thresholds:** 90s → 180s → 270s escalating nudges
- **Dominance threshold:** >50% of recent messages triggers rebalancing
- **Primary model running:** Groq `llama-3.1-8b-instant` (OpenAI `gpt-4o-mini` optional)
- **Ports:** Frontend 3000, Backend 5000
- **Repo layout:** `server/` (Flask backend), `client/frontend/` (React), `supabase/` (SQL migrations), `docs/` (architecture & guides)
</content>
</invoke>
