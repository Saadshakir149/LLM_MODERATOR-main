# Implementation Plan: Supabase Integration & Auto Room Assignment

## Current Status

✅ **Completed**:
- Database schema designed
- Supabase migration files created
- SQL query reference documentation
- Python Supabase client module (`supabase_client.py`)
- Project directory structure organized
- Comprehensive documentation (setup, architecture)
- Dependencies updated (`requirements.txt`)

❌ **Remaining Work**:
- Update Flask app (`app.py`) to use Supabase instead of in-memory storage
- Implement auto room assignment logic
- Create `/join/{mode}` endpoints for simple access
- Add session tracking
- Frontend updates for new URL structure
- Testing and validation

---

## Phase 1: Backend Database Integration

### Task 1.1: Refactor Room Class to Use Supabase

**File**: `server/app.py`

**Changes Needed**:
1. Remove in-memory `rooms` dictionary
2. Update `Room` class to work with Supabase
3. Replace all in-memory operations with database calls

**Code Changes**:

```python
# OLD (in-memory):
rooms: Dict[str, Room] = {}

# NEW (database):
from supabase_client import (
    get_room,
    create_room,
    update_room_status,
    add_participant,
    add_message,
    get_chat_history,
    get_participants
)

# Remove Room class entirely, use database functions
```

**Effort**: 2-3 hours

---

### Task 1.2: Update Socket.IO Event Handlers

**File**: `server/app.py`

**Events to Update**:

#### `create_room` event:
```python
@socketio.on("create_room")
def create_room_handler(data):
    user = data.get("user_name")
    mode = data.get("moderatorMode", "active")

    # Create room in database
    room = create_room(mode=mode, story_id=get_random_story_id())

    # Add creator as participant
    participant = add_participant(
        room_id=room['id'],
        display_name=user,
        socket_id=request.sid
    )

    join_room(room['id'])

    # Send welcome message
    add_message(
        room_id=room['id'],
        sender_name="Moderator",
        message_text=WELCOME_MESSAGE,
        message_type="system"
    )

    emit("joined_room", {"room_id": room['id']}, to=request.sid)
    emit("room_created", {"room_id": room['id'], "mode": mode})

    # Start session tracking
    if mode == "active":
        start_silence_monitor(room['id'])
```

#### `join_room` event:
```python
@socketio.on("join_room")
def join_room_handler(data):
    room_id = data.get("room_id")
    user_name = data.get("user_name")

    # Get room from database
    room = get_room(room_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return

    # Add participant
    participant = add_participant(
        room_id=room_id,
        display_name=user_name,
        socket_id=request.sid
    )

    join_room(room_id)

    # Send chat history
    history = get_chat_history(room_id)
    emit("chat_history", {"chat_history": history}, to=request.sid)

    # Start story if enough participants
    participants = get_participants(room_id)
    if len(participants) >= 2:
        # Start story...
        pass
```

#### `send_message` event:
```python
@socketio.on("send_message")
def send_message_handler(data):
    room_id = data.get("room_id")
    sender = data.get("sender")
    msg = data.get("message", "").strip()

    # Get room and participant
    room = get_room(room_id)
    participant = get_participant_by_socket(request.sid)

    # Store message in database
    message = add_message(
        room_id=room_id,
        participant_id=participant['id'] if participant else None,
        sender_name=sender,
        message_text=msg,
        message_type="chat"
    )

    # Broadcast to all in room
    emit("receive_message", {
        "sender": sender,
        "message": msg
    }, room=room_id)

    # Handle AI intervention (active mode)
    if room['mode'] == 'active' and not room['story_finished']:
        # ... AI logic
        pass
```

**Effort**: 3-4 hours

---

### Task 1.3: Update Story Progression Logic

**Files**: `server/app.py`

**Functions to Update**:
- `advance_story_chunk()` - Update story progress in database
- `passive_continue_story()` - Use database for progress tracking
- `start_silence_monitor()` - Query database for room state

**Key Changes**:
```python
def advance_story_chunk(room_id: str):
    # Get room from database
    room = get_room(room_id)

    if room['story_finished']:
        return

    # ... story logic ...

    # Update progress in database
    update_story_progress(
        room_id=room_id,
        progress=new_progress,
        finished=is_last
    )

    # Add moderator message to database
    add_message(
        room_id=room_id,
        sender_name="Moderator",
        message_text=ai_response,
        message_type="moderator",
        metadata={"story_progress": new_progress}
    )
```

**Effort**: 2-3 hours

---

## Phase 2: Auto Room Assignment

### Task 2.1: Create Auto-Assignment Endpoint

**File**: `server/app.py`

**New Flask Route**:

```python
from flask import redirect, render_template_string

@app.route("/join/<mode>")
def auto_join_room(mode: str):
    """Auto-assign user to available room or create new one."""

    if mode not in ['active', 'passive']:
        return {"error": "Invalid mode. Use 'active' or 'passive'"}, 400

    # Get or create room
    from supabase_client import get_or_create_room
    room = get_or_create_room(mode=mode)

    # Redirect to frontend chat room
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return redirect(f"{frontend_url}/chat/{room['id']}")
```

**Effort**: 1 hour

---

### Task 2.2: Update Auto-Join Logic in Frontend

**File**: `client/frontend/src/App.js`

**New Route**:

```jsx
import { useParams, useNavigate } from 'react-router-dom';

function AutoJoinRoom() {
  const { mode } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    // Call backend to get/create room
    fetch(`http://localhost:5000/join/${mode}`)
      .then(res => res.json())
      .then(data => {
        navigate(`/chat/${data.room_id}`);
      });
  }, [mode]);

  return <div>Finding available room...</div>;
}

// In App.js:
<Route path="/join/:mode" element={<AutoJoinRoom />} />
```

**Effort**: 1-2 hours

---

### Task 2.3: Create Shareable Links UI

**File**: `client/frontend/src/components/RoomCreation.js`

**Add Link Generation**:

```jsx
function RoomCreation() {
  const activeLink = `${window.location.origin}/join/active`;
  const passiveLink = `${window.location.origin}/join/passive`;

  return (
    <div>
      <h2>Quick Join Links</h2>
      <div>
        <p>Active Mode: <a href={activeLink}>{activeLink}</a></p>
        <button onClick={() => navigator.clipboard.writeText(activeLink)}>
          Copy Link
        </button>
      </div>
      <div>
        <p>Passive Mode: <a href={passiveLink}>{passiveLink}</a></p>
        <button onClick={() => navigator.clipboard.writeText(passiveLink)}>
          Copy Link
        </button>
      </div>
    </div>
  );
}
```

**Effort**: 1 hour

---

## Phase 3: Session Tracking

### Task 3.1: Add Session Management

**File**: `server/app.py`

**When to Create Session**:
```python
# When story starts (2+ participants)
from supabase_client import create_session

participants = get_participants(room_id)
if len(participants) >= 2:
    create_session(
        room_id=room_id,
        mode=room['mode'],
        participant_count=len(participants),
        story_id=room['story_id']
    )
```

**When to End Session**:
```python
# When story finishes
if is_last_chunk:
    from supabase_client import end_session
    end_session(room_id, metadata={
        "completion_type": "story_finished"
    })
```

**Effort**: 2 hours

---

## Phase 4: Testing & Validation

### Task 4.1: Manual Testing

**Test Cases**:
1. ✅ Create room via `/join/active` → Should auto-assign
2. ✅ Second user joins same link → Should join existing room
3. ✅ Fourth user joins → Should create new room (max 3 per room)
4. ✅ Send messages → Should appear in Supabase `messages` table
5. ✅ Story progression → Should update `rooms.story_progress`
6. ✅ Complete story → Should create session record
7. ✅ Reconnect after disconnect → Should restore chat history

**Effort**: 2-3 hours

---

### Task 4.2: Database Verification

**Supabase Dashboard Checks**:
1. Check `rooms` table has correct data
2. Check `participants` are auto-named ("Student 1", "Student 2")
3. Check `messages` have timestamps and metadata
4. Check `sessions` have correct durations
5. Verify triggers are working (participant count auto-updates)

**Effort**: 1 hour

---

## Phase 5: Documentation Updates

### Task 5.1: Update README

**File**: `README.md`

**Add Section**:
- Quick start with auto-join links
- How to share links with participants
- Database setup instructions

**Effort**: 30 minutes

---

### Task 5.2: Create Research Guide

**File**: `docs/RESEARCH_GUIDE.md`

**Content**:
- How to export data from Supabase
- CSV export for analysis
- Common SQL queries for research
- Data privacy considerations

**Effort**: 1-2 hours

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| **Phase 1** | Backend Database Integration | 7-10 hours |
| **Phase 2** | Auto Room Assignment | 3-4 hours |
| **Phase 3** | Session Tracking | 2 hours |
| **Phase 4** | Testing & Validation | 3-4 hours |
| **Phase 5** | Documentation | 1.5-2.5 hours |
| **Total** | | **16.5-22.5 hours** |

*Note: This is for one experienced developer. Adjust based on your team.*

---

## Team Task Distribution

If multiple people are working:

**Developer 1 (Backend Focus)**:
- Phase 1: Database integration
- Phase 3: Session tracking

**Developer 2 (Frontend Focus)**:
- Phase 2: Auto-join UI
- Task 2.3: Shareable links

**Developer 3 (QA/Docs)**:
- Phase 4: Testing
- Phase 5: Documentation

---

## Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing functionality | Medium | High | Create feature branch, test thoroughly |
| Supabase rate limits | Low | Medium | Use connection pooling, monitor usage |
| Data loss during migration | Low | High | Backup current data, test on staging first |
| Socket.IO conflicts with DB | Low | Medium | Use transactions, handle race conditions |

---

## Success Criteria

✅ Users can join via simple links (`/join/active`, `/join/passive`)
✅ No manual room ID sharing required
✅ All conversations stored in Supabase
✅ Data persists across server restarts
✅ Session statistics calculated automatically
✅ No breaking changes to existing features
✅ Documentation updated

---

## Next Steps

1. **Set up Supabase** (if not done): Follow `docs/setup/SUPABASE_SETUP.md`
2. **Create feature branch**: `git checkout -b feature/supabase-integration`
3. **Start with Phase 1, Task 1.1**: Refactor Room class
4. **Test incrementally**: After each task, verify it works
5. **Commit frequently**: Small commits are easier to debug

---

## Questions to Resolve

Before starting implementation:
- [ ] What should happen if a room is full? (Currently: create new room)
- [ ] Should we limit total concurrent rooms?
- [ ] How long should rooms stay "waiting" before cleanup?
- [ ] Should we allow users to choose their own names or always auto-generate?
- [ ] What analytics do you want to track for research?

---

## Support

If you get stuck:
- Check `supabase_client.py` for available database functions
- Review SQL queries in `supabase/queries/`
- Test database operations in Supabase SQL Editor
- Ask team for code review before merging
