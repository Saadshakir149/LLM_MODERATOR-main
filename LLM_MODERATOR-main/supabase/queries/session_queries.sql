-- =====================================================
-- Session & Research Data Queries
-- =====================================================

-- Query: Create new session
-- Purpose: Initialize session tracking when room becomes active
INSERT INTO sessions (room_id, mode, participant_count, story_id, started_at, metadata)
VALUES ($1, $2, $3, $4, NOW(), $5)
RETURNING id, room_id, mode, started_at;

-- Query: End session
-- Purpose: Finalize session with statistics
UPDATE sessions
SET
    ended_at = NOW(),
    duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at)),
    message_count = (SELECT COUNT(*) FROM messages WHERE room_id = $1),
    metadata = metadata || $2::jsonb
WHERE room_id = $1 AND ended_at IS NULL
RETURNING id, ended_at, duration_seconds, message_count;

-- Query: Get session by ID
-- Purpose: Retrieve complete session information
SELECT
    id,
    room_id,
    mode,
    participant_count,
    message_count,
    story_id,
    duration_seconds,
    started_at,
    ended_at,
    metadata
FROM sessions
WHERE id = $1;

-- Query: Get all sessions for room
-- Purpose: Handle multiple sessions in same room
SELECT
    id,
    mode,
    participant_count,
    message_count,
    story_id,
    duration_seconds,
    started_at,
    ended_at
FROM sessions
WHERE room_id = $1
ORDER BY started_at ASC;

-- Query: Get sessions by mode
-- Purpose: Research analysis by moderation type
SELECT
    id,
    room_id,
    participant_count,
    message_count,
    story_id,
    duration_seconds,
    started_at,
    ended_at,
    metadata
FROM sessions
WHERE mode = $1
ORDER BY started_at DESC
LIMIT $2;

-- Query: Get session statistics
-- Purpose: Aggregate analytics
SELECT
    mode,
    COUNT(*) as total_sessions,
    AVG(participant_count) as avg_participants,
    AVG(message_count) as avg_messages,
    AVG(duration_seconds) as avg_duration_seconds,
    MIN(started_at) as first_session,
    MAX(started_at) as last_session
FROM sessions
WHERE ended_at IS NOT NULL
GROUP BY mode;

-- Query: Get detailed session data for export
-- Purpose: Complete session export with all related data
SELECT
    s.id as session_id,
    s.room_id,
    s.mode,
    s.story_id,
    s.participant_count,
    s.message_count,
    s.duration_seconds,
    s.started_at,
    s.ended_at,
    s.metadata as session_metadata,
    json_agg(
        json_build_object(
            'participant_id', p.id,
            'display_name', p.display_name,
            'joined_at', p.joined_at,
            'is_moderator', p.is_moderator
        )
        ORDER BY p.joined_at
    ) as participants,
    (
        SELECT json_agg(
            json_build_object(
                'message_id', m.id,
                'sender', m.sender_name,
                'message', m.message_text,
                'type', m.message_type,
                'timestamp', m.created_at,
                'metadata', m.metadata
            )
            ORDER BY m.created_at
        )
        FROM messages m
        WHERE m.room_id = s.room_id
    ) as messages
FROM sessions s
LEFT JOIN participants p ON p.room_id = s.room_id
WHERE s.id = $1
GROUP BY s.id;

-- Query: Export research data snapshot
-- Purpose: Create exportable data for research
INSERT INTO research_data (session_id, room_id, export_format, data_snapshot)
SELECT
    $1,
    s.room_id,
    $2,
    json_build_object(
        'session_id', s.id,
        'mode', s.mode,
        'story_id', s.story_id,
        'duration_seconds', s.duration_seconds,
        'started_at', s.started_at,
        'ended_at', s.ended_at,
        'participants', (
            SELECT json_agg(
                json_build_object(
                    'display_name', p.display_name,
                    'joined_at', p.joined_at,
                    'message_count', (SELECT COUNT(*) FROM messages WHERE participant_id = p.id)
                )
            )
            FROM participants p WHERE p.room_id = s.room_id
        ),
        'messages', (
            SELECT json_agg(
                json_build_object(
                    'timestamp', m.created_at,
                    'sender', m.sender_name,
                    'message', m.message_text,
                    'type', m.message_type
                )
                ORDER BY m.created_at
            )
            FROM messages m WHERE m.room_id = s.room_id
        ),
        'metadata', s.metadata
    )
FROM sessions s
WHERE s.id = $1
RETURNING id, session_id, export_format, created_at;

-- Query: Get all research exports
-- Purpose: List available data exports
SELECT
    id,
    session_id,
    export_format,
    created_at
FROM research_data
ORDER BY created_at DESC
LIMIT $1;

-- Query: Get research export by session
-- Purpose: Retrieve exported data
SELECT
    id,
    session_id,
    room_id,
    export_format,
    data_snapshot,
    created_at
FROM research_data
WHERE session_id = $1
ORDER BY created_at DESC
LIMIT 1;

-- Query: Bulk export sessions for date range
-- Purpose: Export multiple sessions for research analysis
SELECT
    s.id as session_id,
    s.mode,
    s.story_id,
    s.participant_count,
    s.message_count,
    s.duration_seconds,
    s.started_at,
    s.metadata,
    (
        SELECT COUNT(*) FROM messages
        WHERE room_id = s.room_id AND message_type = 'moderator'
    ) as moderator_intervention_count
FROM sessions s
WHERE
    s.started_at >= $1
    AND s.started_at <= $2
    AND s.ended_at IS NOT NULL
ORDER BY s.started_at;

-- Query: Delete old research exports
-- Purpose: Data retention management
DELETE FROM research_data
WHERE created_at < NOW() - INTERVAL '2 years'
RETURNING id;
