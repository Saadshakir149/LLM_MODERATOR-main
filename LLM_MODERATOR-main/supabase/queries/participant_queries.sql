-- =====================================================
-- Participant Management Queries
-- =====================================================

-- Query: Add participant to room
-- Purpose: Register new participant
INSERT INTO participants (room_id, display_name, socket_id, is_moderator)
VALUES ($1, $2, $3, $4)
RETURNING id, room_id, display_name, joined_at;

-- Query: Get next available participant name
-- Purpose: Auto-generate names like "Student 1", "Student 2"
-- Note: This is handled in Python, but here's the logic
SELECT
    'Student ' || (COUNT(*) + 1)::text as next_name
FROM participants
WHERE
    room_id = $1
    AND is_moderator = false;

-- Query: Get all participants in room
-- Purpose: List room members
SELECT
    id,
    display_name,
    socket_id,
    is_moderator,
    joined_at,
    last_active_at
FROM participants
WHERE room_id = $1
ORDER BY joined_at ASC;

-- Query: Get participant by socket ID
-- Purpose: Map Socket.IO connections to participants
SELECT
    id,
    room_id,
    display_name,
    is_moderator,
    joined_at
FROM participants
WHERE socket_id = $1;

-- Query: Update participant socket ID
-- Purpose: Handle reconnections
UPDATE participants
SET socket_id = $2
WHERE id = $1
RETURNING id, socket_id;

-- Query: Update last activity
-- Purpose: Track participant engagement
UPDATE participants
SET last_active_at = NOW()
WHERE id = $1;

-- Query: Get participant count in room
-- Purpose: Check if room is full
SELECT COUNT(*) as count
FROM participants
WHERE room_id = $1;

-- Query: Remove participant from room
-- Purpose: Handle disconnections
DELETE FROM participants
WHERE id = $1
RETURNING room_id;

-- Query: Get inactive participants
-- Purpose: Clean up abandoned connections
SELECT
    id,
    room_id,
    display_name,
    last_active_at
FROM participants
WHERE
    last_active_at < NOW() - INTERVAL '10 minutes'
    AND is_moderator = false;

-- Query: Get participant activity summary
-- Purpose: Research analytics
SELECT
    p.id,
    p.display_name,
    p.joined_at,
    p.last_active_at,
    COUNT(m.id) as message_count,
    EXTRACT(EPOCH FROM (p.last_active_at - p.joined_at)) as active_duration_seconds
FROM participants p
LEFT JOIN messages m ON m.participant_id = p.id
WHERE p.room_id = $1
GROUP BY p.id
ORDER BY p.joined_at;
