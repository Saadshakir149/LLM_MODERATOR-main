# Admin Panel Guide

Complete guide to using the LLM Moderator Admin Panel for managing rooms, settings, and viewing research data.

---

## Overview

The Admin Panel provides a comprehensive interface to:
- **View real-time statistics** across all rooms and sessions
- **Monitor active rooms** and conversations in real-time
- **Manage settings** from the database (no more editing code!)
- **View conversation history** for any room
- **Export data** for research analysis

**Access**: `http://localhost:3000/admin`

---

## Setup

### 1. Run Database Migration

First, run the admin settings migration:

1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `supabase/migrations/002_admin_settings.sql`
3. Paste and click "Run"
4. Verify tables created: `settings`, `admin_logs`

### 2. Restart Backend

The backend now loads configuration from the database:

```bash
cd server
python app.py
```

You should see:
```
✅ Admin API registered at /admin
📝 Loading configuration from database...
📝 Config: Active Step=1, Passive Step=1
```

### 3. Access Admin Panel

Open: `http://localhost:3000/admin`

---

## Features

### Dashboard Tab

**Overview Statistics**:
- Total rooms (active, waiting, completed)
- Total sessions by mode
- Total messages by type
- Session averages (participants, messages, duration)

**Auto-refresh**: Stats automatically refresh every 10 seconds

---

### Rooms Tab

**View All Rooms**:
- See all rooms with status, mode, participant count
- Filter by status: All, Waiting, Active, Completed
- View room details and conversations

**Room Actions**:
- Click "View" to see full room details
- See participant list
- View complete conversation history
- Monitor live conversations (auto-refreshes)

**Room Information Shown**:
- Room ID
- Mode (active/passive)
- Status (waiting/active/completed)
- Current participants / max participants
- Story being discussed
- Created timestamp

---

### Settings Tab

**All Configuration in One Place**:
- Moderator settings (welcome messages, endings)
- Story progression (chunk sizes for active/passive)
- Timing (silence intervals, intervention windows)
- Room settings (max participants, timeouts)
- Feature flags (enable/disable TTS, STT)
- AI settings (model, temperature, max tokens)

**How to Edit Settings**:
1. Click "Edit" next to any setting
2. Change the value
3. Click "Save"
4. Setting is immediately updated in database
5. **Restart backend** to apply changes

**Settings Categories**:
- **Moderator**: Welcome and ending messages
- **Story**: Chunk sizes for progression
- **Timing**: Intervention and silence windows
- **Room**: Participant limits and timeouts
- **Features**: Toggle TTS/STT functionality
- **AI**: OpenAI model configuration

---

### Room Detail View

When you click "View" on a room, you see:

**Room Metadata**:
- Room ID, mode, status
- Participant count
- Message count
- Story progress

**Participants List**:
- Display names
- Join timestamps
- Online status

**Full Conversation**:
- Complete message history
- Color-coded (moderator vs students)
- Timestamps for each message
- Scrollable view

---

## Admin API Endpoints

The admin panel uses these backend endpoints:

### Statistics
- `GET /admin/stats` - Overall statistics

### Rooms
- `GET /admin/rooms` - List all rooms
- `GET /admin/rooms?status=active` - Filter by status
- `GET /admin/rooms?mode=passive` - Filter by mode
- `GET /admin/rooms/<id>` - Get room details with messages

### Settings
- `GET /admin/settings` - Get all settings
- `GET /admin/settings/<key>` - Get specific setting
- `PUT /admin/settings/<key>` - Update setting value

### Data Export
- `GET /admin/export/sessions` - Export session data
- `GET /admin/export/sessions?start_date=2026-01-01` - Export with date filter

### Admin Logs
- `GET /admin/logs` - View admin activity log

---

## Common Tasks

### Change Story Chunk Size

1. Go to Admin Panel → Settings tab
2. Find "ACTIVE_STORY_STEP" or "PASSIVE_STORY_STEP"
3. Click "Edit"
4. Change value (e.g., from 1 to 2)
5. Click "Save"
6. **Restart backend** to apply

### Change Intervention Timing

1. Go to Settings tab
2. Find "ACTIVE_INTERVENTION_WINDOW_SECONDS"
3. Edit value (e.g., change from 20 to 30 seconds)
4. Save
5. Restart backend

### Monitor Active Rooms

1. Go to Rooms tab
2. Filter: "Active"
3. Click "View" on any room
4. See live conversation
5. Page auto-refreshes every 10 seconds

### Export Research Data

**Via API**:
```bash
curl http://localhost:5000/admin/export/sessions > sessions.json
```

**Via Supabase Dashboard**:
1. Go to Supabase → Table Editor
2. Select `sessions` table
3. Click "Export" → CSV

---

## Settings Reference

### Moderator Settings

| Setting | Default | Description |
|---------|---------|-------------|
| WELCOME_MESSAGE | "Welcome everyone! I'm the Moderator." | Initial message sent to all participants |
| ACTIVE_ENDING_MESSAGE | "✨ We have reached the end of the story." | Message when story ends in active mode |

### Story Settings

| Setting | Default | Description |
|---------|---------|-------------|
| ACTIVE_STORY_STEP | 1 | Number of sentences per chunk in active mode |
| PASSIVE_STORY_STEP | 1 | Number of sentences per chunk in passive mode |

### Timing Settings

| Setting | Default | Description |
|---------|---------|-------------|
| PASSIVE_SILENCE_SECONDS | 10 | Seconds before intervention in passive mode |
| ACTIVE_SILENCE_SECONDS | 20 | Seconds before intervention in active mode |
| STORY_CHUNK_INTERVAL | 10 | Seconds between chunks in passive mode |
| ACTIVE_INTERVENTION_WINDOW_SECONDS | 20 | Intervention window for active mode |
| PASSIVE_INTERVENTION_WINDOW_SECONDS | 10 | Intervention window for passive mode |

### Room Settings

| Setting | Default | Description |
|---------|---------|-------------|
| MAX_PARTICIPANTS_PER_ROOM | 3 | Maximum participants per room |
| ROOM_IDLE_TIMEOUT_MINUTES | 60 | Minutes before idle rooms cleaned up |

### Feature Flags

| Setting | Default | Description |
|---------|---------|-------------|
| ENABLE_TTS | true | Enable text-to-speech |
| ENABLE_STT | true | Enable speech-to-text |
| ENABLE_AUTO_START_SINGLE_USER | true | Allow story start with 1 user (testing) |

### AI Settings

| Setting | Default | Description |
|---------|---------|-------------|
| OPENAI_CHAT_MODEL | gpt-4o-mini | OpenAI model for moderation |
| OPENAI_TEMPERATURE | 0.3 | AI temperature (0.0-1.0) |
| OPENAI_MAX_TOKENS | 1500 | Max tokens per response |

---

## Best Practices

### During Research Sessions

1. **Before sessions start**:
   - Check settings are configured correctly
   - Verify story chunk sizes are appropriate
   - Test intervention timings

2. **During sessions**:
   - Monitor Rooms tab for active sessions
   - Check participant counts
   - Watch for any issues in conversations

3. **After sessions**:
   - Review completed rooms
   - Export session data
   - Analyze conversation patterns

### Settings Management

1. **Always test changes** in a test room first
2. **Document settings changes** in admin logs
3. **Restart backend** after changing settings
4. **Keep backups** of working configurations

### Data Export

1. **Regular exports**: Export data weekly
2. **Backup before changes**: Export before modifying settings
3. **Use date filters**: Export specific date ranges for analysis

---

## Troubleshooting

### Admin Panel Not Loading

**Check**:
1. Backend running? `python app.py`
2. Migration run? Check Supabase for `settings` table
3. CORS enabled? Backend allows `localhost:3000`

**Logs**:
```
✅ Admin API registered at /admin
```

### Settings Not Updating

**Issue**: Changed setting but no effect

**Solution**:
1. Verify setting saved in Supabase `settings` table
2. **Restart backend** - settings loaded on startup
3. Check backend logs for "Loading configuration from database"

### Room Data Not Showing

**Issue**: Rooms tab empty but rooms exist

**Solution**:
1. Check backend logs for errors
2. Verify Supabase connection
3. Check `rooms` table in Supabase dashboard
4. Try "Refresh" button in admin panel

### Cannot Edit Settings

**Issue**: Edit button doesn't work

**Solution**:
1. Check browser console for errors
2. Verify admin API endpoints responding: `curl http://localhost:5000/admin/settings`
3. Check CORS configuration

---

## Security Notes

**Current Setup** (Development):
- ⚠️ No authentication required
- ⚠️ Admin panel open to anyone with URL
- ✅ Suitable for local research environment

**For Production**:
- Add admin authentication
- Restrict `/admin` routes to authorized users
- Use environment-based access control
- Enable audit logging

---

## Admin Activity Logging

All admin actions are logged in `admin_logs` table:

**Logged Actions**:
- Setting updates
- Room views
- Data exports
- Configuration changes

**View Logs**:
- Admin Panel → (future Logs tab)
- Supabase Dashboard → `admin_logs` table

---

## Future Enhancements

Planned features:
- [ ] Admin authentication
- [ ] Real-time room monitoring (WebSocket)
- [ ] Bulk setting updates
- [ ] Custom data export formats
- [ ] Analytics dashboard with charts
- [ ] Participant management tools

---

## Quick Reference

**URLs**:
- Admin Panel: `http://localhost:3000/admin`
- Admin API: `http://localhost:5000/admin/*`
- Supabase Dashboard: Your Supabase URL

**Key Files**:
- Migration: `supabase/migrations/002_admin_settings.sql`
- Backend API: `server/admin_api.py`
- Frontend UI: `client/frontend/src/components/AdminDashboard.js`

**Common Commands**:
```bash
# View settings
curl http://localhost:5000/admin/settings

# Update setting
curl -X PUT http://localhost:5000/admin/settings/ACTIVE_STORY_STEP \
  -H "Content-Type: application/json" \
  -d '{"value": "2"}'

# Get stats
curl http://localhost:5000/admin/stats

# Export sessions
curl http://localhost:5000/admin/export/sessions > data.json
```

---

## Support

For issues:
1. Check Supabase `admin_logs` table
2. Check backend `server_debug.log`
3. Check browser console for frontend errors
4. Verify database migration ran successfully

For questions, see:
- `docs/TESTING_GUIDE.md` - Testing procedures
- `docs/LOGGING_GUIDE.md` - Understanding logs
- `docs/architecture/database-schema.md` - Database structure
