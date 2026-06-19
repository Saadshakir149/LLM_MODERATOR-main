-- =====================================================
-- Migration: 006_event_log_and_snapshots
-- Purpose: Research-integrity hardening (Priority 8).
--   * event_log            — append-only GROUND TRUTH of everything that happened
--                            (8.4). Every subsystem writes here.
--   * room_state_snapshots — frozen room_state + final metrics at session end (8.1),
--                            stamped with the immutable experiment condition (8.2).
-- Apply in the Supabase SQL editor. Writers are best-effort / fail-safe, so the app
-- degrades gracefully until this is applied.
-- =====================================================

-- ----- event_log (append-only ground truth) -----
CREATE TABLE IF NOT EXISTS event_log (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    session_id UUID,
    experiment_condition VARCHAR(20),     -- no_moderator | passive_moderator | active_moderator
    event_type VARCHAR(40) NOT NULL,      -- message | stt | tts | intervention | state_update | session
    payload_json JSONB,
    "timestamp" TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_log_room_ts ON event_log(room_id, "timestamp");
CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type);

-- ----- room_state_snapshots (frozen + versioned at session end / periodic) -----
CREATE TABLE IF NOT EXISTS room_state_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    session_id UUID,
    experiment_condition VARCHAR(20),
    full_room_state_json JSONB,           -- the operational room_state at snapshot time
    final_metrics_json JSONB,             -- frozen research_metrics_v2 output (incl. timelines)
    snapshot_kind VARCHAR(20) DEFAULT 'final',  -- final | periodic
    "timestamp" TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rss_room_id ON room_state_snapshots(room_id);

COMMENT ON TABLE event_log IS 'Append-only ground-truth event stream; the authoritative research dataset (P8.4).';
COMMENT ON TABLE room_state_snapshots IS 'Frozen room_state + final metrics per session, stamped with experiment_condition (P8.1/8.2).';
