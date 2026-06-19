# Database Schema Documentation

## Overview
This document describes the PostgreSQL database schema for the LLM Moderator research platform, hosted on Supabase.

## Design Principles
- **No user authentication** - Anonymous participation for research
- **Data collection focus** - All conversations stored for analysis
- **Auto-room assignment** - Users automatically assigned to available rooms
- **Mode-based rooms** - Separate rooms for Active and Passive moderation modes

---

## Tables

### 1. `rooms`
Stores information about chat rooms.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique room identifier |
| `mode` | VARCHAR(10) | NOT NULL, CHECK (mode IN ('active', 'passive')) | Moderation mode |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'waiting', CHECK (status IN ('waiting', 'active', 'completed')) | Room state |
| `max_participants` | INTEGER | NOT NULL, DEFAULT 3 | Maximum participants allowed |
| `current_participants` | INTEGER | NOT NULL, DEFAULT 0 | Current number of participants |
| `story_id` | VARCHAR(100) | | Story being discussed |
| `story_progress` | INTEGER | DEFAULT 0 | Current story sentence index |
| `story_finished` | BOOLEAN | DEFAULT false | Whether story is complete |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Room creation timestamp |
| `started_at` | TIMESTAMPTZ | | When conversation started |
| `completed_at` | TIMESTAMPTZ | | When conversation ended |

**Indexes:**
- `idx_rooms_status_mode` on `(status, mode)` - Fast lookup for available rooms
- `idx_rooms_created_at` on `(created_at)` - Time-based queries

---

### 2. `participants`
Stores anonymous participant information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique participant identifier |
| `room_id` | UUID | NOT NULL, FOREIGN KEY → rooms(id) ON DELETE CASCADE | Associated room |
| `display_name` | VARCHAR(50) | NOT NULL | Anonymous display name (e.g., "Student 1") |
| `socket_id` | VARCHAR(100) | | Current Socket.IO session ID |
| `is_moderator` | BOOLEAN | DEFAULT false | Whether this is the AI moderator |
| `joined_at` | TIMESTAMPTZ | DEFAULT NOW() | Join timestamp |
| `last_active_at` | TIMESTAMPTZ | DEFAULT NOW() | Last activity timestamp |

**Indexes:**
- `idx_participants_room_id` on `(room_id)` - Fast participant lookup
- `idx_participants_socket_id` on `(socket_id)` - Socket connection tracking

**Constraints:**
- `unique_display_name_per_room` UNIQUE `(room_id, display_name)` - No duplicate names in room

---

### 3. `messages`
Stores all chat messages for research analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique message identifier |
| `room_id` | UUID | NOT NULL, FOREIGN KEY → rooms(id) ON DELETE CASCADE | Associated room |
| `participant_id` | UUID | FOREIGN KEY → participants(id) ON DELETE SET NULL | Message sender |
| `sender_name` | VARCHAR(50) | NOT NULL | Display name of sender |
| `message_text` | TEXT | NOT NULL | Message content |
| `message_type` | VARCHAR(20) | DEFAULT 'chat', CHECK (message_type IN ('chat', 'system', 'story', 'moderator')) | Message category |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Message timestamp |
| `metadata` | JSONB | | Additional data (e.g., story progress, intervention type) |

**Indexes:**
- `idx_messages_room_id_created_at` on `(room_id, created_at)` - Chronological message retrieval
- `idx_messages_created_at` on `(created_at)` - Time-based analysis
- `idx_messages_metadata` GIN `(metadata)` - JSON queries

---

### 4. `sessions`
Tracks complete conversation sessions for research analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique session identifier |
| `room_id` | UUID | NOT NULL, FOREIGN KEY → rooms(id) ON DELETE CASCADE | Associated room |
| `mode` | VARCHAR(10) | NOT NULL | Moderation mode |
| `participant_count` | INTEGER | NOT NULL | Number of participants |
| `message_count` | INTEGER | DEFAULT 0 | Total messages exchanged |
| `story_id` | VARCHAR(100) | | Story discussed |
| `duration_seconds` | INTEGER | | Session duration |
| `started_at` | TIMESTAMPTZ | NOT NULL | Session start |
| `ended_at` | TIMESTAMPTZ | | Session end |
| `metadata` | JSONB | | Session-level analytics (interventions, participation rates, etc.) |

**Indexes:**
- `idx_sessions_mode_started_at` on `(mode, started_at)` - Research queries by mode and time
- `idx_sessions_metadata` GIN `(metadata)` - Analytics queries

---

### 5. `research_data`
Aggregated data for research analysis and export.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique record identifier |
| `session_id` | UUID | FOREIGN KEY → sessions(id) ON DELETE CASCADE | Associated session |
| `room_id` | UUID | FOREIGN KEY → rooms(id) ON DELETE CASCADE | Associated room |
| `export_format` | VARCHAR(20) | DEFAULT 'json' | Data format |
| `data_snapshot` | JSONB | NOT NULL | Complete session data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Export timestamp |

**Indexes:**
- `idx_research_data_session_id` on `(session_id)` - Session lookups

---

## Relationships

```
rooms (1) ──< (many) participants
rooms (1) ──< (many) messages
rooms (1) ──< (many) sessions
sessions (1) ──< (many) research_data

participants (1) ──< (many) messages
```

---

## Row Level Security (RLS)

For this research project, we'll disable RLS since there's no user authentication. However, API keys will be kept server-side only.

**Configuration:**
```sql
-- Disable RLS for all tables (research project with no auth)
ALTER TABLE rooms DISABLE ROW LEVEL SECURITY;
ALTER TABLE participants DISABLE ROW LEVEL SECURITY;
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE research_data DISABLE ROW LEVEL SECURITY;
```

---

## Data Retention

- All data retained indefinitely for research purposes
- Backup recommendations: Daily automated backups via Supabase
- Export capabilities: CSV, JSON, Excel formats for analysis

---

## Future Enhancements

1. **feedback** table - Store participant feedback
2. **interventions** table - Track AI moderator interventions
3. **analytics_cache** table - Pre-computed analytics
4. Partitioning for large-scale data (by month/year)
