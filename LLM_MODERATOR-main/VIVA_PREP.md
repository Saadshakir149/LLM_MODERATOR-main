# Viva + Lab Exam + Demo — Study Kit (LLM Moderator)

---

## PART A — DEMO READINESS CHECKLIST (do this tonight)

**1. Backend runs**
```powershell
cd C:\Users\cvalley\Downloads\LLM_MODERATOR-main\LLM_MODERATOR-main\server
python app.py
```
Look for: `Running on http://127.0.0.1:5000` and `✅ Groq client initialized`.

**2. Frontend runs (second terminal)**
```powershell
cd C:\Users\cvalley\Downloads\LLM_MODERATOR-main\LLM_MODERATOR-main\client\frontend
npm start
```
Open **http://localhost:3000** (NOT 5000 — 5000 is API-only and returns 404 on `/`).

**3. Pre-flight checks**
- [ ] `.env` in `server/` has a valid `GROQ_API_KEY` (the app uses Groq).
- [ ] Internet works (Supabase + Groq are cloud services).
- [ ] Can create a room and send a message; AI moderator replies.
- [ ] To simulate 3 students: open 3 browser tabs (or use the auto-join — it fills a room of 3).
- [ ] Know your fallback line if Wi-Fi dies: *"It needs Supabase + Groq cloud APIs; here's the architecture and code"* + show the running logs/screenshots.

**4. Have these open in your editor for the demo**
- `server/app.py` (Socket.IO events, Room logic)
- `server/prompts.py` (moderator decision logic)
- `server/research_metrics.py` (Gini, entropy, conflict)
- `server/data_retriever.py` (Desert scenarios + expert ranking)
- `supabase/migrations/001_initial_schema.sql` and `003_research_rq_metrics.sql`

---

## PART B — 60-SECOND DEMO SCRIPT (say this while clicking)
1. "This is an AI-moderated group-discussion research platform. Three students solve the **Desert Survival** task — ranking 12 items for survival."
2. *(create/join room)* "Rooms auto-fill to 3 participants, then the session starts with a randomly chosen scenario and a 15-minute timer."
3. *(type a message)* "Messages go over **Socket.IO (WebSockets)** to the Flask backend, get stored in **Supabase**, and broadcast to everyone in real time."
4. *(let AI reply)* "The **AI moderator** doesn't reply to everything — it decides an intervention type: invite a silent student, balance a dominator over 50%, de-escalate conflict, give time warnings, or summarize."
5. "Everything is logged, and we compute **research metrics** — Gini coefficient, entropy, conflict/repair rate, ranking accuracy — to compare an **Active** vs **Passive** moderator. That's the actual research contribution."
6. *(open /admin or AdminDashboard)* "Admins can monitor rooms and **export research data**."

---

## PART C — PROJECT-SPECIFIC VIVA Q&A

**Q: What is your project and its purpose?**
A research platform to test whether an LLM can effectively moderate small-group discussions. Groups of 3 solve the Desert Survival ranking task; an AI moderator facilitates. We measure whether moderation improves participation equality, conflict resolution, on-task focus, and decision accuracy — by comparing an Active vs a Passive moderator (an A/B experiment).

**Q: Why the "Desert Survival" task?**
It's a well-established group decision-making exercise with a known **expert ranking**, so we can objectively score how good the group's final answer is. It naturally produces disagreement and negotiation — exactly what we want to study.

**Q: What are Active vs Passive modes?**
- **Active:** AI proactively facilitates (invites silent members, balances dominators, de-escalates, refocuses). This is the treatment group.
- **Passive:** AI barely intervenes. This is the control/baseline. Comparing the two isolates the *effect of moderation*.

**Q: How does the AI decide when to intervene? (key question)**
It's **state-based**, not reply-to-everything. In `prompts.py` it selects an `intervention_type`:
- `answer_question` (a student @mentioned the moderator)
- `invite_silent` (someone idle ≥ 90s; escalates at 180s, 270s)
- `balance_dominance` (one person > 50% of recent messages)
- `time_warning`, `summarize`, `appreciate`
- de-escalation when 2+ speakers show conflict cues.
Each type gets a custom prompt + temperature.

**Q: What is the Gini coefficient and why use it?**
A measure of inequality from 0 to 1. Here it measures **inequality of speaking shares**: 0 = everyone talks equally, 1 = one person dominates. Lower Gini = fairer participation. Formula implemented in `research_metrics.py` (`calculate_gini_coefficient`).

**Q: What is Shannon entropy here?**
Normalized (0–1) measure of how *evenly* participation is spread. High entropy = balanced discussion. It complements Gini. Computed with `-Σ p·log2(p)` divided by `log2(n)`.

**Q: How do you detect conflict and "repair"?**
Keyword-based heuristics. Conflict keywords ("disagree", "wrong", "stupid"...) flag conflict turns; repair keywords ("good point", "fair enough", "agreed"...) flag reconciliation. A repair is paired to a recent conflict within 2 minutes → gives **repair rate** and **time-to-repair** (RQ2).

**Q: How is ranking accuracy computed?**
The group's final item ranking is compared to the scenario's **expert ranking** by summing absolute position differences (`compare_with_expert_ranking`). Smaller total difference = more accurate.

**Q: Explain your architecture / tech stack.**
3-tier: **React** frontend (port 3000) ↔ **Flask + Socket.IO** backend (port 5000) ↔ **Supabase/PostgreSQL**. The backend calls an **LLM** (Groq Llama-3.1-8b-instant, with OpenAI GPT-4o-mini optional). Real-time via WebSockets; persistence + research tables in Postgres.

**Q: Why Socket.IO / WebSockets instead of REST?**
Chat needs **bidirectional, real-time** push — the server must send messages to clients without them polling. WebSockets keep a persistent connection; Socket.IO adds reconnection and fallbacks. REST (request/response) can't push.

**Q: Why Flask?**
Lightweight Python web framework, integrates cleanly with Flask-SocketIO and the AI/Python ecosystem (Groq/OpenAI SDKs).

**Q: Why Supabase / PostgreSQL?**
Managed Postgres with a simple Python client, free tier, JSONB for flexible metadata, triggers/indexes for analytics — ideal for storing research data.

**Q: Walk me through what happens when a user sends a message.**
1. Frontend emits `send_message` over Socket.IO.
2. Backend saves it to `messages` in Supabase.
3. Backend broadcasts `receive_message` to all clients in the room.
4. (Active mode) Backend evaluates whether/how the AI should intervene; if so it calls the LLM, saves and broadcasts the moderator reply, logs the intervention.

**Q: How do you handle 3 users joining the same room?**
Auto-join finds a `waiting` room with space (or creates one). A Postgres **trigger** auto-increments `current_participants`. When it hits 3, the session starts (`status=active`), the scenario is pinned, the 15-min timer thread starts.

**Q: Database design — main tables?**
`rooms`, `participants`, `messages`, `sessions` (core) + `research_metrics`, `participant_metrics`, `moderator_interventions`, `conflict_episodes` (research). UUID primary keys, foreign keys with `ON DELETE CASCADE`, triggers for counts/activity, GIN indexes on JSONB.

**Q: Why did GET / give a 404 earlier?**
Because the Flask backend only serves API + Socket.IO routes — there's no `/` page. The UI is the separate React app on port 3000. (Good to mention — shows you understand the client/server split.)

**Q: How is the LLM integrated? What if OpenAI is down?**
A provider-agnostic layer: it prefers OpenAI if a key exists, otherwise uses **Groq** as fallback. `chatbot.py` (GroqChatbot) wraps the API with retries and canned fallback replies so the session never crashes.

**Q: What are the 5 research questions?**
RQ1 participation equality (Gini/entropy), RQ2 conflict & repair, RQ3 dominance reduction, RQ4 on-task focus, RQ5 responsiveness (latency after interventions).

**Q: Limitations / future work?**
In-memory per-server Socket.IO (no horizontal scaling yet → add Redis adapter); conflict detection is keyword-based (could use a classifier); small sample; could add more task types and statistical analysis dashboards.

**Q: What was the hardest part?**
Designing the moderator's *intervention logic* so it helps without spamming — handled with state-based selection + per-person cooldowns and silence thresholds (90/180/270s).

---

## PART D — GENERAL CS / LAB CONCEPTS (likely in viva)

**WebSocket vs HTTP:** HTTP = request/response, client-initiated, stateless. WebSocket = persistent, full-duplex, server can push. Used for real-time apps (chat, live updates).

**REST API:** Stateless client-server over HTTP using verbs GET/POST/PUT/DELETE on resources. Your `/admin/*` endpoints are REST.

**Frontend vs Backend:** Frontend (React) = UI in the browser. Backend (Flask) = business logic, AI calls, DB access. They communicate over HTTP + WebSocket.

**SPA (Single Page Application):** React loads once and updates the DOM dynamically via routing instead of full page reloads.

**SQL basics:** Primary key (unique row id), Foreign key (link between tables), `ON DELETE CASCADE` (delete children when parent deleted), index (speeds up lookups), JOIN (combine tables). JSONB = binary JSON column in Postgres.

**Database trigger:** A function that runs automatically on INSERT/UPDATE/DELETE. You use one to keep `current_participants` accurate.

**Environment variables / .env:** Store secrets (API keys) outside code so they aren't committed; loaded via `python-dotenv`.

**CORS:** Browser security that blocks cross-origin requests; you allow the frontend origin so :3000 can call :5000.

**API key / authentication:** Secret token to call an external service (Groq/OpenAI/Supabase). Kept server-side only.

**Concurrency / threading:** The backend uses background threads (timers, silence monitor) so it can track time and act while still serving requests. Socket.IO async mode = `threading` (because eventlet breaks on Python 3.12).

**LLM (Large Language Model):** A neural network trained on text that predicts/generates language. You prompt it with context and it returns a moderator reply.

**Prompt engineering:** Crafting the system/user prompt to get the desired AI behavior. Each intervention type has a tailored prompt and temperature.

**Temperature:** LLM randomness control. Low = focused/deterministic; high = creative/varied. You lower it for precise interventions (e.g., 0.62 for balancing dominance).

**Gini coefficient / Shannon entropy:** Statistical inequality and evenness measures (defined above).

**MVC-ish separation:** UI (React) / logic (Flask) / data (Postgres) — separation of concerns.

---

## PART E — 30-SECOND SELF-INTRO (memorize)
"My project is an **AI-moderated group discussion platform** built to research whether a large language model can facilitate teamwork. Three students solve the **Desert Survival** ranking task in a real-time chat; an **AI moderator** keeps participation fair, de-escalates conflict, and keeps them on task. It's built with **React, Flask + Socket.IO, Supabase/PostgreSQL, and the Groq LLM**, and it computes research metrics like the **Gini coefficient** and **conflict-repair rate** to compare an active versus passive moderator."
</content>
