-- =====================================================
-- Migration: 004_voice_recordings
-- Purpose: Link each voice (push-to-talk) message to its audio object in the
--          PRIVATE Supabase Storage bucket `voice-recordings`.
--
-- Contract:
--   * Text messages create NO rows here.
--   * The messages row holds the FINAL text shown in the transcript (message_text).
--   * voice_recordings.transcript_text = the RAW Speech-to-Text output.
--   * Audio object lives at  voice-recordings/{room_id}/{message_id}.webm
--   * Bucket is PRIVATE; playback is served only via short-lived signed URLs.
-- Apply in the Supabase SQL editor.
-- =====================================================

-- ----- voice_recordings -----
CREATE TABLE IF NOT EXISTS voice_recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,            -- {room_id}/{message_id}.webm within the bucket
    duration_ms INTEGER,                   -- client-measured recording length
    mime_type VARCHAR(100) DEFAULT 'audio/webm',
    stt_model VARCHAR(80),                 -- e.g. gpt-4o-mini-transcribe
    transcript_text TEXT,                  -- RAW STT output (final text lives on messages.message)
    edited_after_stt BOOLEAN DEFAULT false,-- true if the sent text differs from the raw transcript
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_recordings_room_id ON voice_recordings(room_id);
CREATE INDEX IF NOT EXISTS idx_voice_recordings_message_id ON voice_recordings(message_id);

-- One audio object per message.
CREATE UNIQUE INDEX IF NOT EXISTS uq_voice_recordings_message_id ON voice_recordings(message_id);

COMMENT ON TABLE voice_recordings IS 'Audio for voice messages; bytes in private bucket voice-recordings, played via signed URLs.';
COMMENT ON COLUMN voice_recordings.transcript_text IS 'RAW STT output; messages.message holds the final (possibly edited) text.';
COMMENT ON COLUMN voice_recordings.edited_after_stt IS 'true when the sent message text differs from the raw transcript.';

-- ----- PRIVATE storage bucket -----
-- public = false keeps it private; the server uses the service role key (bypasses RLS)
-- and never mints public URLs — only short-lived signed URLs for playback.
INSERT INTO storage.buckets (id, name, public)
VALUES ('voice-recordings', 'voice-recordings', false)
ON CONFLICT (id) DO NOTHING;
