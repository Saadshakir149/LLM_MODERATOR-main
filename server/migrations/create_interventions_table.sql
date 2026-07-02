-- ============================================================
-- SQL Migration: Schema for moderator_interventions Table
-- Enables Telemetry and Intervention Tracking for RQ1-RQ5
-- ============================================================

CREATE TABLE IF NOT EXISTS public.moderator_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id TEXT NOT NULL REFERENCES public.rooms(id) ON DELETE CASCADE,
    intervention_type TEXT NOT NULL,
    target_user TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT,
    research_question TEXT DEFAULT 'RQ5',
    expected_effect TEXT,
    ranking_state_before JSONB DEFAULT '{}'::jsonb,
    ranking_state_after JSONB DEFAULT '{}'::jsonb,
    response_latency FLOAT DEFAULT 0.0,
    success BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast query lookups by room and type
CREATE INDEX IF NOT EXISTS idx_moderator_interventions_room_id ON public.moderator_interventions(room_id);
CREATE INDEX IF NOT EXISTS idx_moderator_interventions_type ON public.moderator_interventions(intervention_type);
