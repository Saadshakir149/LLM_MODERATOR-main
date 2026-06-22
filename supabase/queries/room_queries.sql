-- =====================================================
-- Room Management Queries
-- =====================================================

-- Query: Find available room by mode
-- Purpose: Get room with space for auto-assignment
-- Returns: Room with < max_participants
SELECT
    id,
    mode,
    status,
    current_participants,
    max_participants,
    story_id,
    created_at
FROM rooms
WHERE
    mode = $1
    AND status = 'waiting'
    AND current_participants < max_participants
ORDER BY created_at ASC
LIMIT 1;

-- Query: Create new room
-- Purpose: Initialize new chat room
INSERT INTO rooms (mode, story_id)
VALUES ($1, $2)
RETURNING id, mode, status, current_participants, max_participants, created_at;

-- Query: Get room by ID
-- Purpose: Retrieve complete room information
SELECT
    id,
    mode,
    status,
    current_participants,
    max_participants,
    story_id,
    story_progress,
    story_finished,
    created_at,
    started_at,
    completed_at
FROM rooms
WHERE id = $1;

-- Query: Update room status
-- Purpose: Change room state (waiting → active → completed)
UPDATE rooms
SET
    status = $2,
    started_at = CASE WHEN $2 = 'active' AND started_at IS NULL THEN NOW() ELSE started_at END,
    completed_at = CASE WHEN $2 = 'completed' THEN NOW() ELSE completed_at END
WHERE id = $1
RETURNING id, status, started_at, completed_at;

-- Query: Update story progress
-- Purpose: Track story advancement
UPDATE rooms
SET
    story_progress = $2,
    story_finished = $3
WHERE id = $1;

-- Query: Get active rooms count by mode
-- Purpose: Analytics - monitor room usage
SELECT
    mode,
    COUNT(*) as room_count,
    SUM(current_participants) as total_participants
FROM rooms
WHERE status IN ('waiting', 'active')
GROUP BY mode;

-- Query: Mark room as completed
-- Purpose: Finalize room when story ends
UPDATE rooms
SET
    status = 'completed',
    completed_at = NOW(),
    story_finished = true
WHERE id = $1;

-- Query: Get room statistics
-- Purpose: Research analytics
SELECT
    r.id,
    r.mode,
    r.story_id,
    r.current_participants,
    COUNT(DISTINCT p.id) as participant_count,
    COUNT(m.id) as message_count,
    r.created_at,
    r.started_at,
    r.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(r.completed_at, NOW()) - r.started_at)) as duration_seconds
FROM rooms r
LEFT JOIN participants p ON p.room_id = r.id
LEFT JOIN messages m ON m.room_id = r.id
WHERE r.id = $1
GROUP BY r.id;

-- Query: Clean up old waiting rooms
-- Purpose: Remove stale rooms (older than 1 hour with no activity)
DELETE FROM rooms
WHERE
    status = 'waiting'
    AND created_at < NOW() - INTERVAL '1 hour'
    AND current_participants = 0
RETURNING id;
