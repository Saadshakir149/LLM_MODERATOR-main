# Testing Guide - Supabase Integration

Complete testing checklist for the LLM Moderator with Supabase integration.

---

## Prerequisites

Before testing, ensure:
- ✅ Supabase project created and migration run
- ✅ `.env` file configured with Supabase credentials
- ✅ Backend dependencies installed (`pip install -r requirements.txt`)
- ✅ Frontend dependencies installed (`npm install`)
- ✅ Both servers running (backend on :5000, frontend on :3000)

---

## Quick Verification

### 1. Check Supabase Connection

```bash
cd server
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -c "from supabase_client import supabase; print('✅ Supabase connected!')"
```

**Expected**: "✅ Supabase connected!"

### 2. Check Backend Server

```bash
cd server
python app.py
```

**Expected**:
```
🚀 LLM Moderator server with Supabase starting...
Frontend URL: http://localhost:3000
 * Running on http://0.0.0.0:5000
```

### 3. Check Frontend

```bash
cd client/frontend
npm start
```

**Expected**: Browser opens to `http://localhost:3000`

---

## Test Scenarios

### Test 1: Auto-Join Active Mode

**Objective**: Verify auto room assignment works for active mode

**Steps**:
1. Open browser: `http://localhost:3000/join/active`
2. Should see "Finding Available Room..." loading screen
3. Should redirect to `/chat/{room_id}`
4. You should be assigned name "Student 1" (or similar)

**Verify in Supabase**:
- Go to Supabase dashboard → Table Editor → `rooms`
- Should see new room with `mode='active'`, `status='waiting'`
- Go to `participants` table
- Should see your participant record

**✅ Pass Criteria**:
- Auto-redirects to chat room
- Room created in database
- Participant added to database

---

### Test 2: Auto-Join Passive Mode

**Objective**: Verify auto room assignment works for passive mode

**Steps**:
1. Open new browser window/tab
2. Go to: `http://localhost:3000/join/passive`
3. Should redirect to chat room in passive mode

**Verify in Supabase**:
- Check `rooms` table for `mode='passive'` room

**✅ Pass Criteria**:
- Auto-redirects to chat room
- Room created with passive mode
- Participant added

---

### Test 3: Multiple Users in Same Room

**Objective**: Verify multiple users can join same room

**Steps**:
1. Open Window 1: `http://localhost:3000/join/active`
2. Note the room_id in URL
3. Open Window 2: `http://localhost:3000/join/active`
4. Should join **same room** as Window 1 (max 3 participants)

**Verify**:
- Both windows show same chat room
- Check `participants` table: should see 2 participants with same `room_id`
- Check `rooms` table: `current_participants` should be 2

**✅ Pass Criteria**:
- Second user joins existing room (not creates new)
- Both users see welcome message
- Participant count updates correctly

---

### Test 4: Room Full - Create New Room

**Objective**: Verify new room created when existing is full

**Steps**:
1. Open 3 windows, all join: `http://localhost:3000/join/active`
2. All 3 should join same room (max capacity)
3. Open 4th window: `http://localhost:3000/join/active`
4. 4th user should get **different room_id**

**Verify in Supabase**:
- Should see 2 rooms in `rooms` table
- First room: `current_participants=3`
- Second room: `current_participants=1`

**✅ Pass Criteria**:
- 4th user gets new room
- Old room stays at 3 participants
- New room created automatically

---

### Test 5: Send Messages

**Objective**: Verify messages stored in database

**Steps**:
1. Join a room (use auto-join or manual)
2. Type message: "Hello world!"
3. Send message

**Verify in Supabase**:
- Go to `messages` table
- Should see your message with:
  - Correct `room_id`
  - Your `participant_id`
  - `sender_name` (e.g., "Student 1")
  - `message_text` = "Hello world!"
  - `message_type` = "chat"
  - Timestamp in `created_at`

**✅ Pass Criteria**:
- Message appears in chat
- Message stored in database
- All fields populated correctly

---

### Test 6: Story Progression (Active Mode)

**Objective**: Verify story advances and is tracked in database

**Steps**:
1. Join active mode room with 2+ users
2. Wait for moderator to start story
3. Wait 20 seconds (silence monitor triggers)
4. Moderator should send story chunk

**Verify in Supabase**:
- Check `rooms` table: `story_progress` should increment
- Check `messages` table: moderator messages with `message_type='moderator'`
- Check `metadata` field: should contain `{"story_progress": X}`

**✅ Pass Criteria**:
- Story progresses
- Progress tracked in database
- Moderator messages stored

---

### Test 7: Story Progression (Passive Mode)

**Objective**: Verify passive mode auto-advances

**Steps**:
1. Join passive mode room with 2+ users
2. Story should start automatically
3. Wait 10 seconds
4. Next story chunk should appear

**Verify**:
- Story chunks appear every 10 seconds
- Messages stored in database
- `story_progress` increments

**✅ Pass Criteria**:
- Auto-advancement works
- No manual interaction needed
- Progress tracked

---

### Test 8: Session Tracking

**Objective**: Verify session created and ended properly

**Steps**:
1. Join room with 2+ users
2. Story should start
3. Wait for story to complete (or manually progress to end)

**Verify in Supabase**:
- Go to `sessions` table
- Should see session with:
  - Correct `room_id`
  - `mode` matching room mode
  - `participant_count` = 2 (or more)
  - `started_at` timestamp
  - `ended_at` timestamp (when story completes)
  - `message_count` > 0
  - `duration_seconds` calculated

**✅ Pass Criteria**:
- Session created when story starts
- Session ended when story completes
- All statistics populated

---

### Test 9: Chat History Persistence

**Objective**: Verify chat history loaded from database

**Steps**:
1. Join room, send several messages
2. Close browser tab
3. Manually rejoin same room (use room_id in URL)
4. Should see all previous messages

**✅ Pass Criteria**:
- Chat history loads from database
- All messages display correctly
- Order preserved

---

### Test 10: Shareable Links UI

**Objective**: Verify shareable links work

**Steps**:
1. Go to `http://localhost:3000/`
2. Should see "Quick Join Links" section at top
3. Click "Copy" button for Active Mode link
4. Open new incognito window
5. Paste link and navigate
6. Should join active mode room

**✅ Pass Criteria**:
- Links visible on homepage
- Copy button works
- Links navigate correctly

---

## Database Verification Checklist

After running all tests, verify in Supabase dashboard:

### Rooms Table
- [ ] Multiple rooms created
- [ ] `mode` field set correctly (active/passive)
- [ ] `status` field updated (waiting → active → completed)
- [ ] `current_participants` matches actual count
- [ ] `story_progress` increments
- [ ] Timestamps populated

### Participants Table
- [ ] Multiple participants created
- [ ] `display_name` auto-generated (e.g., "Student 1", "Student 2")
- [ ] `room_id` links to correct room
- [ ] `socket_id` populated
- [ ] `last_active_at` updates

### Messages Table
- [ ] All messages stored
- [ ] Different `message_type` values (chat, system, story, moderator)
- [ ] `metadata` field contains JSON
- [ ] Timestamps in order

### Sessions Table
- [ ] Sessions created when story starts
- [ ] `ended_at` populated when story ends
- [ ] `message_count` matches actual messages
- [ ] `duration_seconds` calculated

---

## Common Issues

### Issue: "Missing Supabase credentials"

**Solution**:
```bash
cd server
cat .env  # verify SUPABASE_URL and SUPABASE_SERVICE_KEY are set
```

### Issue: "Room not found"

**Solution**:
- Check room exists in database
- Verify room_id in URL matches database
- Check database connection

### Issue: Messages not appearing

**Solution**:
- Check browser console for errors
- Verify Socket.IO connected
- Check backend logs: `server/server_debug.log`
- Verify Supabase credentials

### Issue: Story not progressing

**Solution**:
- Ensure 2+ participants in room
- Check room `status` is 'active'
- Verify background tasks running
- Check backend logs

### Issue: Auto-join creates new room every time

**Solution**:
- Check `current_participants < max_participants` logic
- Verify participant count updating
- Check database trigger working

---

## Performance Testing

### Load Test: Multiple Concurrent Users

**Steps**:
1. Open 10 browser tabs
2. All navigate to `/join/active`
3. Verify:
   - Max 3 per room
   - 4 rooms created (3+3+3+1)
   - All rooms tracked in database

### Stress Test: Message Volume

**Steps**:
1. Join room with 3 users
2. Send 100 messages rapidly
3. Verify:
   - All messages stored
   - No duplicates
   - Correct order
   - Performance acceptable

---

## Data Export Test

### Export Session Data

**SQL Query** (run in Supabase SQL Editor):

```sql
-- Get all data for a specific session
SELECT
    s.id as session_id,
    s.mode,
    s.participant_count,
    s.message_count,
    s.duration_seconds,
    r.story_id,
    json_agg(
        json_build_object(
            'sender', m.sender_name,
            'message', m.message_text,
            'timestamp', m.created_at
        )
        ORDER BY m.created_at
    ) as messages
FROM sessions s
JOIN rooms r ON r.id = s.room_id
LEFT JOIN messages m ON m.room_id = s.room_id
WHERE s.id = 'your-session-id-here'
GROUP BY s.id, s.mode, s.participant_count, s.message_count, s.duration_seconds, r.story_id;
```

**✅ Pass Criteria**:
- Query returns complete session data
- All messages included
- JSON format valid

---

## Final Checklist

Before marking complete:

- [ ] All 10 test scenarios pass
- [ ] Database verification complete
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] Shareable links work
- [ ] Auto-join assigns correctly
- [ ] Messages persist across refreshes
- [ ] Story progression works (both modes)
- [ ] Session tracking complete
- [ ] Data exportable from Supabase

---

## Reporting Issues

If you find bugs:

1. Note exact steps to reproduce
2. Check backend logs: `server/server_debug.log`
3. Check browser console for errors
4. Screenshot Supabase table data
5. Create GitHub issue with all details

---

## Success Criteria

✅ **Fully Working System**:
- Users can join via shareable links
- Rooms auto-assign (max 3 per room)
- All conversations stored in database
- Story progression works
- Sessions tracked
- Data persists across server restarts
- No data loss
- Ready for research data collection

---

## Next Steps After Testing

Once all tests pass:

1. Deploy to production environment
2. Set up automated backups (Supabase)
3. Configure production URLs
4. Share links with research participants
5. Monitor data collection
6. Export data for analysis

See `docs/DEPLOYMENT.md` (coming soon) for production deployment guide.
