-- =====================================================
-- Migration: 005_research_metrics_v2
-- Purpose: Authoritative research instrumentation (Priority 6).
--   * research_metrics_v2  — long/tidy format (one row per metric value), ideal for
--     time-series + per-participant analysis in R/pandas.
--   * room_metrics_summary — wide format (one row per room), ideal for cross-condition
--     statistical comparison (No / Passive / Active moderator).
-- Apply in the Supabase SQL editor. Export endpoints compute on the fly too, so these
-- tables are for persistence/snapshotting, not a hard dependency.
-- =====================================================

-- ----- research_metrics_v2 (long / tidy) -----
CREATE TABLE IF NOT EXISTS research_metrics_v2 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id VARCHAR(100),          -- NULL for room-level metrics
    metric_name VARCHAR(80) NOT NULL,
    metric_value DOUBLE PRECISION,
    "timestamp" TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rmv2_room_id ON research_metrics_v2(room_id);
CREATE INDEX IF NOT EXISTS idx_rmv2_metric ON research_metrics_v2(metric_name);

-- ----- room_metrics_summary (wide / one row per room) -----
CREATE TABLE IF NOT EXISTS room_metrics_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    session_id UUID,
    condition VARCHAR(20),                -- no_moderator | passive | active
    gini DOUBLE PRECISION,                -- turn-based Gini (participation inequality)
    entropy DOUBLE PRECISION,             -- normalized turn entropy
    dominance_gap DOUBLE PRECISION,
    turn_count INTEGER,
    avg_turn_duration DOUBLE PRECISION,   -- ms (NULL when no audio durations)
    avg_silence_duration DOUBLE PRECISION,-- seconds
    consensus_score DOUBLE PRECISION,     -- final consensus proxy (see metrics docs)
    intervention_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rms_room_id ON room_metrics_summary(room_id);
CREATE INDEX IF NOT EXISTS idx_rms_condition ON room_metrics_summary(condition);

COMMENT ON TABLE research_metrics_v2 IS 'Authoritative tidy research metrics (one row per metric); see research_metrics_v2.py.';
COMMENT ON TABLE room_metrics_summary IS 'One wide row per room for cross-condition statistical analysis.';
COMMENT ON COLUMN room_metrics_summary.consensus_score IS 'Final lexical consensus PROXY; validated consensus comes from the summary pipeline (P4).';
