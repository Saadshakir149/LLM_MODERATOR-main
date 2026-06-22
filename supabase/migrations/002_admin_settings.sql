-- =====================================================
-- Migration: 002_admin_settings
-- Description: Add settings table for admin panel configuration
-- Author: Research Team
-- Date: 2026-01-03
-- =====================================================

-- =====================================================
-- Table: settings
-- Purpose: Store all configuration settings (replaces env variables)
-- =====================================================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    data_type VARCHAR(20) DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'boolean', 'float')),
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system'
);

-- Index for fast key lookups
CREATE INDEX idx_settings_key ON settings(key);
CREATE INDEX idx_settings_category ON settings(category);

-- Comments
COMMENT ON TABLE settings IS 'Configuration settings for admin panel control';
COMMENT ON COLUMN settings.key IS 'Unique setting identifier (e.g., ACTIVE_STORY_STEP)';
COMMENT ON COLUMN settings.value IS 'Setting value as text (converted based on data_type)';
COMMENT ON COLUMN settings.data_type IS 'Type for conversion: string, integer, boolean, float';
COMMENT ON COLUMN settings.category IS 'Setting category: moderator, timing, features, etc.';

-- =====================================================
-- Insert Default Settings
-- =====================================================

-- Moderator Settings
INSERT INTO settings (key, value, data_type, category, description) VALUES
('WELCOME_MESSAGE', 'Welcome everyone! I''m the Moderator.', 'string', 'moderator', 'Initial welcome message sent to all participants'),
('ACTIVE_ENDING_MESSAGE', '✨ We have reached the end of the story.', 'string', 'moderator', 'Message sent when story ends in active mode');

-- Story Progression Settings
INSERT INTO settings (key, value, data_type, category, description) VALUES
('ACTIVE_STORY_STEP', '1', 'integer', 'story', 'Number of sentences per chunk in active mode'),
('PASSIVE_STORY_STEP', '1', 'integer', 'story', 'Number of sentences per chunk in passive mode');

-- Timing Settings
INSERT INTO settings (key, value, data_type, category, description) VALUES
('PASSIVE_SILENCE_SECONDS', '10', 'integer', 'timing', 'Seconds of silence before intervention in passive mode'),
('ACTIVE_SILENCE_SECONDS', '20', 'integer', 'timing', 'Seconds of silence before intervention in active mode'),
('STORY_CHUNK_INTERVAL', '10', 'integer', 'timing', 'Seconds between story chunks in passive mode'),
('ACTIVE_INTERVENTION_WINDOW_SECONDS', '20', 'integer', 'timing', 'Intervention window for active mode'),
('PASSIVE_INTERVENTION_WINDOW_SECONDS', '10', 'integer', 'timing', 'Intervention window for passive mode');

-- Room Settings
INSERT INTO settings (key, value, data_type, category, description) VALUES
('MAX_PARTICIPANTS_PER_ROOM', '3', 'integer', 'room', 'Maximum number of participants allowed per room'),
('ROOM_IDLE_TIMEOUT_MINUTES', '60', 'integer', 'room', 'Minutes before idle rooms are cleaned up');

-- Feature Flags
INSERT INTO settings (key, value, data_type, category, description) VALUES
('ENABLE_TTS', 'true', 'boolean', 'features', 'Enable text-to-speech functionality'),
('ENABLE_STT', 'true', 'boolean', 'features', 'Enable speech-to-text functionality'),
('ENABLE_AUTO_START_SINGLE_USER', 'true', 'boolean', 'features', 'Allow story to start with single participant (for testing)');

-- OpenAI Settings
INSERT INTO settings (key, value, data_type, category, description) VALUES
('OPENAI_CHAT_MODEL', 'gpt-4o-mini', 'string', 'ai', 'OpenAI model for chat moderation'),
('OPENAI_TEMPERATURE', '0.3', 'float', 'ai', 'Temperature for AI responses (0.0-1.0)'),
('OPENAI_MAX_TOKENS', '1500', 'integer', 'ai', 'Maximum tokens for AI responses');

-- =====================================================
-- Function: Update setting timestamp
-- =====================================================
CREATE OR REPLACE FUNCTION update_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update timestamp
CREATE TRIGGER trigger_update_settings_timestamp
BEFORE UPDATE ON settings
FOR EACH ROW
EXECUTE FUNCTION update_settings_timestamp();

-- =====================================================
-- Table: admin_logs
-- Purpose: Track all admin actions
-- =====================================================
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    admin_user VARCHAR(100),
    ip_address VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for admin logs
CREATE INDEX idx_admin_logs_created_at ON admin_logs(created_at DESC);
CREATE INDEX idx_admin_logs_admin_user ON admin_logs(admin_user);
CREATE INDEX idx_admin_logs_action ON admin_logs(action);

-- Comments
COMMENT ON TABLE admin_logs IS 'Audit log of all admin panel actions';
COMMENT ON COLUMN admin_logs.action IS 'Action performed: update_setting, view_room, export_data, etc.';
COMMENT ON COLUMN admin_logs.entity_type IS 'Type of entity affected: setting, room, session, etc.';

-- =====================================================
-- Disable RLS (No auth for research)
-- =====================================================
ALTER TABLE settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_logs DISABLE ROW LEVEL SECURITY;
