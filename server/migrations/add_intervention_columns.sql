-- ============================================================
-- SQL Migration: Add missing columns to moderator_interventions
-- ============================================================

ALTER TABLE public.moderator_interventions 
ADD COLUMN IF NOT EXISTS intervention_type TEXT,
ADD COLUMN IF NOT EXISTS target_user TEXT,
ADD COLUMN IF NOT EXISTS pre_state JSONB,
ADD COLUMN IF NOT EXISTS response_latency FLOAT,
ADD COLUMN IF NOT EXISTS success_flag BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS response_text TEXT;

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_interventions_room_time ON public.moderator_interventions(room_id, created_at);
