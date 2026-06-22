-- =====================================================
-- Migration: 001_initial_schema
-- Description: Create initial database schema for LLM Moderator
-- Author: Research Team
-- Date: 2026-01-03
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Table: rooms
-- Purpose: Store chat room information
-- =====================================================
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mode VARCHAR(10) NOT NULL CHECK (mode IN ('active', 'passive')),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'active', 'completed')),
    max_participants INTEGER NOT NULL DEFAULT 3,
    current_participants INTEGER NOT NULL DEFAULT 0,
    story_id VARCHAR(100),
    story_progress INTEGER DEFAULT 0,
    story_finished BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_participant_count CHECK (current_participants >= 0 AND current_participants <= max_participants)
);

-- Indexes for rooms
CREATE INDEX idx_rooms_status_mode ON rooms(status, mode);
CREATE INDEX idx_rooms_created_at ON rooms(created_at);

-- Comments
COMMENT ON TABLE rooms IS 'Chat rooms for collaborative learning sessions';
COMMENT ON COLUMN rooms.mode IS 'Moderation mode: active (AI engages) or passive (auto-advance)';
COMMENT ON COLUMN rooms.status IS 'Room state: waiting (for participants), active (in session), completed (finished)';

-- =====================================================
-- Table: participants
-- Purpose: Store anonymous participant information
-- =====================================================
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    display_name VARCHAR(50) NOT NULL,
    socket_id VARCHAR(100),
    is_moderator BOOLEAN DEFAULT false,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: no duplicate names in same room
    CONSTRAINT unique_display_name_per_room UNIQUE (room_id, display_name)
);

-- Indexes for participants
CREATE INDEX idx_participants_room_id ON participants(room_id);
CREATE INDEX idx_participants_socket_id ON participants(socket_id);

-- Comments
COMMENT ON TABLE participants IS 'Anonymous participants in chat rooms';
COMMENT ON COLUMN participants.display_name IS 'Auto-generated name like "Student 1" or "Moderator"';
COMMENT ON COLUMN participants.socket_id IS 'Current Socket.IO connection ID for real-time events';

-- =====================================================
-- Table: messages
-- Purpose: Store all chat messages for research
-- =====================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id) ON DELETE SET NULL,
    sender_name VARCHAR(50) NOT NULL,
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'chat' CHECK (message_type IN ('chat', 'system', 'story', 'moderator')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for messages
CREATE INDEX idx_messages_room_id_created_at ON messages(room_id, created_at);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_metadata ON messages USING GIN (metadata);

-- Comments
COMMENT ON TABLE messages IS 'All chat messages stored for research analysis';
COMMENT ON COLUMN messages.message_type IS 'Category: chat (user), system (notifications), story (narrative), moderator (AI)';
COMMENT ON COLUMN messages.metadata IS 'Additional context: story_progress, intervention_type, etc.';

-- =====================================================
-- Table: sessions
-- Purpose: Track complete conversation sessions
-- =====================================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    mode VARCHAR(10) NOT NULL,
    participant_count INTEGER NOT NULL,
    message_count INTEGER DEFAULT 0,
    story_id VARCHAR(100),
    duration_seconds INTEGER,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    metadata JSONB
);

-- Indexes for sessions
CREATE INDEX idx_sessions_mode_started_at ON sessions(mode, started_at);
CREATE INDEX idx_sessions_metadata ON sessions USING GIN (metadata);

-- Comments
COMMENT ON TABLE sessions IS 'Complete conversation sessions for research analysis';
COMMENT ON COLUMN sessions.metadata IS 'Analytics: intervention_count, avg_response_time, participation_rates, etc.';

-- =====================================================
-- Table: research_data
-- Purpose: Aggregated data exports for research
-- =====================================================
CREATE TABLE research_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    export_format VARCHAR(20) DEFAULT 'json',
    data_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for research_data
CREATE INDEX idx_research_data_session_id ON research_data(session_id);

-- Comments
COMMENT ON TABLE research_data IS 'Exported research data snapshots for analysis';
COMMENT ON COLUMN research_data.data_snapshot IS 'Complete session data in JSON format';

-- =====================================================
-- Functions & Triggers
-- =====================================================

-- Function: Update room participant count
CREATE OR REPLACE FUNCTION update_room_participant_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE rooms
        SET current_participants = current_participants + 1
        WHERE id = NEW.room_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE rooms
        SET current_participants = current_participants - 1
        WHERE id = OLD.room_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update participant count
CREATE TRIGGER trigger_update_participant_count
AFTER INSERT OR DELETE ON participants
FOR EACH ROW
EXECUTE FUNCTION update_room_participant_count();

-- Function: Update last_active_at on message
CREATE OR REPLACE FUNCTION update_participant_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE participants
    SET last_active_at = NOW()
    WHERE id = NEW.participant_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Track participant activity
CREATE TRIGGER trigger_participant_activity
AFTER INSERT ON messages
FOR EACH ROW
WHEN (NEW.participant_id IS NOT NULL)
EXECUTE FUNCTION update_participant_activity();

-- Function: Update session message count
CREATE OR REPLACE FUNCTION update_session_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET message_count = message_count + 1
    WHERE room_id = NEW.room_id AND ended_at IS NULL;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Track message count
CREATE TRIGGER trigger_session_message_count
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_session_message_count();

-- =====================================================
-- Disable Row Level Security (No auth for research)
-- =====================================================
ALTER TABLE rooms DISABLE ROW LEVEL SECURITY;
ALTER TABLE participants DISABLE ROW LEVEL SECURITY;
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE research_data DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- Initial Data (Optional)
-- =====================================================
-- None required for initial deployment

-- =====================================================
-- Grants (Adjust based on Supabase service role)
-- =====================================================
-- Grants will be handled by Supabase automatically
