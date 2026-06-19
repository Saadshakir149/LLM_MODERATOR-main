# Logging Guide

The backend now has comprehensive logging to help you track what's happening at every step.

---

## Log File Location

**File**: `server/server_debug.log`

The log file appends (doesn't overwrite), so you can track activity across multiple runs.

---

## Log Icons

Logs use emoji icons for easy scanning:

| Icon | Meaning | Examples |
|------|---------|----------|
| 🚀 | Server starting | Server initialization |
| 🔗 | HTTP endpoint called | `/join/active` called |
| 🔌 | WebSocket connection | Client connected/disconnected |
| 🏗️ | Room creation | Manual room creation |
| 🚪 | Room joining | User joining room |
| 📊 | Room status | Participant count, room state |
| 🎬 | Story starting | Story intro being sent |
| 📖 | Story progression | Story chunk sent |
| 💬 | Chat message | User sent message |
| ✅ | Success | Operation completed successfully |
| ❌ | Error | Operation failed |
| ⚠️ | Warning | Non-critical issue |
| ℹ️ | Info | General information |
| 📝 | Configuration | Config values loaded |
| 🔄 | Loop started | Background task started |
| 👁️ | Monitor started | Silence monitor active |
| ⏹️ | Task stopped | Background task ended |
| 🏁 | Story finished | Story reached the end |
| 🔔 | Intervention | AI moderator intervening |
| 🔊 | TTS | Text-to-speech request |
| 🎤 | STT | Speech-to-text request |
| 📚 | Story selection | Story chosen for room |

---

## Understanding the Flow

### When User Clicks /join/active

You'll see:

```
🔗 /join/active - Auto-join request received
📚 Selected story: the-golden-goose
✅ Room assigned: abc-123-def (mode=active, participants=0)
```

**What this means**: User requested active mode, system selected a story, and assigned an available room.

---

### When User Joins Chat Room

You'll see:

```
🔌 Client connected: xyz789sid
🚪 Join room request: room=abc-123-def, user=None, sid=xyz789sid
📝 Auto-generated name: Student 1
✅ Participant added: Student 1 → room abc-123-def
📜 Sending 1 messages to Student 1
📊 Room abc-123-def: 1 students, status=waiting
🎬 Starting story for room abc-123-def with 1 students
✅ Room abc-123-def status → active
✅ Session created: session-id-456
📖 Sending story intro to room abc-123-def
👁️ Starting silence monitor for room abc-123-def
👁️ Silence monitor started for room abc-123-def
```

**What this means**:
1. WebSocket connected
2. User joined room (no name provided, so auto-generated "Student 1")
3. Participant added to database
4. Chat history sent (just welcome message)
5. Room has 1 student, status is "waiting"
6. Story starts (we allow 1 user for testing now!)
7. Room status changed to "active"
8. Session created in database
9. Story intro sent to chat
10. Silence monitor started (for active mode)

---

### When User Sends Message

You'll see:

```
💬 Message from Student 1 in room abc-123-def: Hello everyone!
✅ Message sent to room abc-123-def
```

**What this means**: Message received and broadcast to all participants in the room.

---

### When Story Progresses (Active Mode)

You'll see:

```
🔔 Silence detected in room abc-123-def, advancing story
📖 Active story chunk 0→1/45 for room abc-123-def
✅ Message sent to room abc-123-def
```

**What this means**: After 20 seconds of silence, moderator intervened and sent story chunk 0→1 (out of 45 total).

---

### When Story Progresses (Passive Mode)

You'll see:

```
🔄 Passive loop started for room abc-123-def
📖 Passive story chunk 0→1/45 for room abc-123-def
📖 Passive story chunk 1→2/45 for room abc-123-def
...
```

**What this means**: Story auto-advances every 10 seconds in passive mode.

---

### When Story Finishes

You'll see:

```
📖 Active story chunk 44→45/45 for room abc-123-def
🏁 Story finished for room abc-123-def
✅ Session ended for room abc-123-def
⏹️ Silence monitor stopped for room abc-123-def
```

**What this means**: Story reached the end, session ended in database, background tasks stopped.

---

## Common Log Patterns

### Successful Room Join

```
🔗 /join/active - Auto-join request received
📚 Selected story: ...
✅ Room assigned: ...
🔌 Client connected: ...
🚪 Join room request: ...
📝 Auto-generated name: Student 1
✅ Participant added: ...
🎬 Starting story for room ...
✅ Room ... status → active
✅ Session created: ...
📖 Sending story intro ...
```

### Error Joining Room

```
🔗 /join/active - Auto-join request received
❌ Error in auto_join_room: [error details]
[Full stack trace]
```

### Multiple Users Joining Same Room

```
🚪 Join room request: room=abc-123, user=None, sid=sid1
📝 Auto-generated name: Student 1
✅ Participant added: Student 1 → room abc-123
📊 Room abc-123: 1 students, status=waiting

🚪 Join room request: room=abc-123, user=None, sid=sid2
📝 Auto-generated name: Student 2
✅ Participant added: Student 2 → room abc-123
📊 Room abc-123: 2 students, status=waiting (or active if story already started)
```

---

## Troubleshooting with Logs

### Problem: Room shows "waiting" but not starting

**Look for**:
```
📊 Room abc-123: X students, status=waiting
```

**If X = 0**: No participants yet (shouldn't happen if you joined)
**If X ≥ 1**: Story should start. Look for:
```
🎬 Starting story for room abc-123 with X students
```

**If you don't see "Starting story"**:
- Check for errors: `❌` symbols
- Check if room status is not "waiting": `ℹ️ Room abc-123 already started`

---

### Problem: Messages not appearing

**Look for**:
```
💬 Message from [name] in room [id]: [message]
```

**If you see this but message doesn't appear in UI**:
- Check frontend console for Socket.IO errors
- Check if Socket.IO is connected: look for `🔌 Client connected`

**If you don't see this log**:
- Message didn't reach backend
- Check frontend console
- Check network requests

---

### Problem: Story not progressing

**Active Mode - Look for**:
```
🔔 Silence detected in room ..., advancing story
📖 Active story chunk X→Y/Total
```

**If missing**: Silence monitor might not be running. Check for:
```
👁️ Silence monitor started for room ...
```

**Passive Mode - Look for**:
```
🔄 Passive loop started for room ...
📖 Passive story chunk X→Y/Total (every 10 seconds)
```

**If missing**: Passive loop not started. Check story start logs.

---

### Problem: Database errors

**Look for**:
```
❌ Error in [function]: [error message]
[Stack trace with file:line numbers]
```

Common issues:
- **"Missing Supabase credentials"**: Check `.env` file
- **"Permission denied"**: Check Supabase service key
- **"Relation does not exist"**: Run database migration
- **"Connection refused"**: Supabase URL wrong or network issue

---

## Reading Stack Traces

When you see an error like:

```
❌ Error in join_room_handler: division by zero
Traceback (most recent call last):
  File "app.py", line 556, in join_room_handler
    x = 1 / 0
ZeroDivisionError: division by zero
```

**How to read it**:
1. **First line**: What function errored and the error type
2. **File/line**: Where the error occurred (`app.py` line 556)
3. **Code**: The actual code that failed
4. **Error type**: Type of error (ZeroDivisionError)

---

## Viewing Logs

### In Terminal (Live)

When you run `python app.py`, logs appear in real-time.

### In Log File

```bash
cd server
tail -f server_debug.log
```

This shows the last lines and updates live.

### Filter Specific Events

```bash
# Show only errors
grep "❌" server_debug.log

# Show only room joins
grep "🚪" server_debug.log

# Show only story progression
grep "📖" server_debug.log

# Show specific room
grep "room abc-123" server_debug.log
```

---

## Log Levels

Current log level: **INFO**

**What you see**:
- ✅ Important operations
- ❌ All errors
- 🔗 HTTP requests
- 💬 Messages
- 📖 Story progression

**What you don't see**:
- Internal Socket.IO details
- Database query details (except errors)
- Verbose debug information

To enable **DEBUG** level (very verbose):

Edit `server/app.py` line 65:
```python
level=logging.DEBUG,  # Change from INFO to DEBUG
```

---

## Example Full Flow

```
============================================================
🚀 LLM Moderator Server Starting
============================================================
✅ FFmpeg configured
📝 Config: Active Step=1, Passive Step=1
📝 Config: Story Interval=10s
📝 Frontend URL: http://localhost:3000
============================================================
🚀 Starting Flask-SocketIO server
📍 Host: 0.0.0.0:5000
🌐 Frontend: http://localhost:3000
============================================================

🔗 /join/active - Auto-join request received
📚 Selected story: the-golden-goose
✅ Room assigned: abc-123-def (mode=active, participants=0)

🔌 Client connected: xyz789sid

🚪 Join room request: room=abc-123-def, user=None, sid=xyz789sid
📝 Auto-generated name: Student 1
✅ Participant added: Student 1 → room abc-123-def
📜 Sending 1 messages to Student 1
📊 Room abc-123-def: 1 students, status=waiting
🎬 Starting story for room abc-123-def with 1 students
✅ Room abc-123-def status → active
✅ Session created: session-456-789
📖 Sending story intro to room abc-123-def
👁️ Starting silence monitor for room abc-123-def
👁️ Silence monitor started for room abc-123-def

💬 Message from Student 1 in room abc-123-def: Hello!
✅ Message sent to room abc-123-def

🔔 Silence detected in room abc-123-def, advancing story
📖 Active story chunk 0→1/45 for room abc-123-def

💬 Message from Student 1 in room abc-123-def: Interesting!
✅ Message sent to room abc-123-def

🔔 Silence detected in room abc-123-def, advancing story
📖 Active story chunk 1→2/45 for room abc-123-def

... (story continues) ...

📖 Active story chunk 44→45/45 for room abc-123-def
🏁 Story finished for room abc-123-def
✅ Session ended for room abc-123-def

⏹️ Silence monitor stopped for room abc-123-def
```

---

## Tips

1. **Keep terminal open** while testing to see logs in real-time
2. **Use emoji search** in your editor to find specific events quickly
3. **Check timestamps** to correlate events with user actions
4. **Save error logs** when reporting issues
5. **Clear log file** periodically if it gets too large:
   ```bash
   > server/server_debug.log
   ```

---

## Next Steps

After reviewing logs:
- If errors appear, check the error message and stack trace
- If story not starting, verify participant count and room status
- If database issues, verify Supabase credentials
- If Socket.IO issues, check frontend console

For more help, see:
- `docs/TESTING_GUIDE.md` - Testing scenarios
- `docs/setup/DEVELOPMENT_SETUP.md` - Setup troubleshooting
