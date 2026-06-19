-- =====================================================
-- Message Management Queries
-- =====================================================

-- Query: Insert new message
-- Purpose: Store chat message
INSERT INTO messages (room_id, participant_id, sender_name, message_text, message_type, metadata)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING id, room_id, sender_name, message_text, created_at;

-- Query: Get room chat history
-- Purpose: Retrieve all messages for a room
SELECT
    id,
    sender_name,
    message_text,
    message_type,
    created_at,
    metadata
FROM messages
WHERE room_id = $1
ORDER BY created_at ASC;

-- Query: Get recent messages
-- Purpose: Load last N messages for participants joining
SELECT
    id,
    sender_name,
    message_text,
    message_type,
    created_at,
    metadata
FROM messages
WHERE room_id = $1
ORDER BY created_at DESC
LIMIT $2;

-- Query: Get messages by type
-- Purpose: Filter specific message categories
SELECT
    id,
    sender_name,
    message_text,
    created_at,
    metadata
FROM messages
WHERE
    room_id = $1
    AND message_type = $2
ORDER BY created_at ASC;

-- Query: Count messages in room
-- Purpose: Track conversation volume
SELECT COUNT(*) as message_count
FROM messages
WHERE room_id = $1;

-- Query: Get moderator interventions
-- Purpose: Research analytics - track AI engagement
SELECT
    id,
    message_text,
    created_at,
    metadata->>'intervention_type' as intervention_type,
    metadata->>'story_progress' as story_progress
FROM messages
WHERE
    room_id = $1
    AND (message_type = 'moderator' OR sender_name = 'Moderator')
ORDER BY created_at ASC;

-- Query: Get participant message statistics
-- Purpose: Analyze individual participation
SELECT
    sender_name,
    COUNT(*) as message_count,
    AVG(LENGTH(message_text)) as avg_message_length,
    MIN(created_at) as first_message,
    MAX(created_at) as last_message
FROM messages
WHERE
    room_id = $1
    AND message_type = 'chat'
    AND sender_name != 'Moderator'
GROUP BY sender_name
ORDER BY message_count DESC;

-- Query: Get conversation timeline
-- Purpose: Export complete conversation with timestamps
SELECT
    m.created_at,
    m.sender_name,
    m.message_text,
    m.message_type,
    p.display_name as participant_name,
    p.is_moderator,
    m.metadata
FROM messages m
LEFT JOIN participants p ON p.id = m.participant_id
WHERE m.room_id = $1
ORDER BY m.created_at ASC;

-- Query: Search messages
-- Purpose: Find specific content in conversations
SELECT
    id,
    room_id,
    sender_name,
    message_text,
    created_at
FROM messages
WHERE
    room_id = $1
    AND message_text ILIKE $2
ORDER BY created_at ASC;

-- Query: Get messages with metadata filter
-- Purpose: Advanced analytics queries
SELECT
    id,
    sender_name,
    message_text,
    created_at,
    metadata
FROM messages
WHERE
    room_id = $1
    AND metadata @> $2::jsonb
ORDER BY created_at ASC;

-- Query: Delete old messages (cleanup)
-- Purpose: Data retention management
DELETE FROM messages
WHERE created_at < NOW() - INTERVAL '1 year'
RETURNING id, room_id;
