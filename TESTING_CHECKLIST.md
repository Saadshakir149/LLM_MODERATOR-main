# LLM Moderator - Testing Checklist

Complete testing guide to verify all features are working correctly.

---

## ✅ Pre-Testing Setup Verification

Before testing features, verify your setup is correct:

### 1. Check Backend is Running
```bash
cd /home/user/LLM_MODERATOR/server
python app.py
```

**Expected Output:**
```
✅ Admin API registered at /admin
📝 Loading configuration from database...
📝 Config: Active Step=1, Passive Step=1
📝 Config: Story Interval=10s
🚀 Starting Flask-SocketIO server
📍 Host: 0.0.0.0:5000
```

**If you see errors:**
- ❌ "Invalid API key" → Check `.env` file has correct Supabase credentials
- ❌ "Module not found" → Run `pip install -r requirements.txt`
- ❌ "Table does not exist" → Run database migrations in Supabase

### 2. Check Frontend is Running
```bash
cd /home/user/LLM_MODERATOR/client/frontend
npm start
```

**Expected:**
- Browser opens to `http://localhost:3000`
- No console errors (check DevTools → Console)

### 3. Check Database Connection

**Test API:**
```bash
curl http://localhost:5000/admin/settings
```

**Expected Response:**
```json
{
  "settings": [
    {
      "key": "ACTIVE_STORY_STEP",
      "value": "1",
      "data_type": "integer",
      ...
    },
    ...
  ]
}
```

**If error:**
- ❌ Connection refused → Backend not running
- ❌ 500 error → Check backend logs for database connection issues

---

## 🧪 Feature Testing Scenarios

---

## Test 1: Admin Panel Access ⭐

### Steps:
1. Open browser to `http://localhost:3000/admin`

### Expected Results:
- ✅ See vertical sidebar with "Admin Panel" header
- ✅ Three navigation items: Shareable Links, Rooms, Settings
- ✅ "Shareable Links" tab is active by default
- ✅ See two link boxes (Active Mode and Passive Mode)

### Success Criteria:
- [ ] Admin panel loads without errors
- [ ] All three tabs are visible
- [ ] Links show correct URLs

### If Failed:
- Check browser console for errors
- Verify backend is running
- Check `/admin` route in App.js

---

## Test 2: Copy Shareable Links ⭐

### Steps:
1. Go to Admin Panel → Shareable Links tab
2. Click "Copy" button next to Active Mode Link
3. Open new incognito/private window
4. Paste URL and press Enter

### Expected Results:
- ✅ Alert shows "✅ Active mode link copied to clipboard!"
- ✅ URL is: `http://localhost:3000/join/active`
- ✅ Pasting in new window redirects to chat room
- ✅ Username is auto-generated (e.g., "Student 123")

### Success Criteria:
- [ ] Copy button works
- [ ] Link is correct format
- [ ] Auto-join works
- [ ] Anonymous username is assigned

### If Failed:
- Check AutoJoin.js component exists
- Verify `/join/:mode` route in App.js
- Check backend logs for room assignment

---

## Test 3: Auto Room Assignment (Single User) ⭐

### Steps:
1. Open `http://localhost:3000/join/active`
2. Wait 5 seconds

### Expected Results:
- ✅ Redirected to `/chat/[room-id]?userName=Student%20XXX`
- ✅ Chat window opens
- ✅ See "waiting for story to begin" OR story starts immediately
- ✅ Room ID is visible at top

### Check Backend Logs:
```
🔗 /join/active - Auto-join request received
✅ Room assigned: [room-id] (mode=active, participants=1)
🚪 User 'Student XXX' joined room [room-id]
```

### Success Criteria:
- [ ] User auto-assigned to room
- [ ] Username is anonymous (Student + number)
- [ ] Chat window loads
- [ ] Backend logs show room assignment

### If Failed:
- Check `/join/:mode` endpoint in app.py
- Verify `find_available_room()` function
- Check Supabase rooms table

---

## Test 4: Multi-User Room Filling ⭐⭐⭐

**This tests if users fill the same room before creating new ones**

### Steps:
1. **User 1**: Open `http://localhost:3000/join/active`
   - Note the Room ID (top of chat window)

2. **User 2**: Open same URL in new incognito window
   - Check if Room ID matches User 1

3. **User 3**: Open same URL in another incognito window
   - Check if Room ID matches User 1 & 2

4. **User 4**: Open same URL in another window
   - This should create a NEW room (previous room is full)

### Expected Results:

**Users 1, 2, 3:**
- ✅ All get the SAME Room ID
- ✅ Each has different username (Student 1, Student 2, Student 3)
- ✅ Each has different color in chat

**User 4:**
- ✅ Gets a DIFFERENT Room ID
- ✅ New room is created (previous was full with 3 users)

### Check Backend Logs:
```
# User 1
✅ Room assigned: abc123 (mode=active, participants=1)

# User 2
✅ Room assigned: abc123 (mode=active, participants=2)  # Same room!

# User 3
✅ Room assigned: abc123 (mode=active, participants=3)  # Same room!

# User 4
🆕 Creating new room (no available rooms)
✅ Room assigned: xyz789 (mode=active, participants=1)  # New room!
```

### Success Criteria:
- [ ] Users 1-3 join same room
- [ ] User 4 gets new room
- [ ] Room participant count increments correctly
- [ ] Backend logs show room reuse

### If Failed:
- Check `find_available_room()` in supabase_client.py
- Verify query searches for `.in_("status", ["waiting", "active"])`
- Check max_participants setting (should be 3)

---

## Test 5: Story Start Behavior ⭐⭐

**Current Setting**: Story starts when 1st user joins

### Steps:
1. Open `http://localhost:3000/join/active`
2. Wait 5 seconds

### Expected Results:
- ✅ Story starts immediately (you see first story chunk)
- ✅ Moderator sends: "Welcome everyone! I'm the Moderator."
- ✅ Story chunk appears (e.g., "Once upon a time...")

### Check Backend Logs:
```
🎬 Starting story for room [room-id] with 1 students
📖 Story chunk sent to [room-id]: "Once upon a time..."
```

### Success Criteria:
- [ ] Story starts with 1 participant
- [ ] Moderator welcome message appears
- [ ] First story chunk is delivered

### To Change This Behavior:
1. Go to Admin Panel → Settings
2. Find `ENABLE_AUTO_START_SINGLE_USER`
3. Change from `true` to `false`
4. Restart backend
5. Now story won't start until 3 users join

---

## Test 6: Color-Coded Chat ⭐⭐

**Tests if each student has unique color**

### Steps:
1. **User 1**: Open `http://localhost:3000/join/active`
   - Send message: "Hello, I'm user 1"
   - Note your color (should be BLUE)

2. **User 2**: Open in new incognito window
   - Send message: "Hello, I'm user 2"
   - Note the color (should be different from User 1)

3. **User 3**: Open in another window
   - Send message: "Hello, I'm user 3"
   - Note the color (should be different from 1 & 2)

### Expected Results:

**User 1 (current user):**
- ✅ Messages have BLUE background
- ✅ Avatar has blue border
- ✅ Username label is blue
- ✅ Messages appear on RIGHT side

**User 2:**
- ✅ Messages have GREEN/PURPLE/PINK background (different color)
- ✅ Avatar has matching border
- ✅ Username label matches message color
- ✅ Messages appear on LEFT side

**User 3:**
- ✅ Different color from User 1 & 2
- ✅ Consistent color across all messages
- ✅ Messages appear on LEFT side

**Moderator:**
- ✅ Messages have YELLOW background
- ✅ Centered in chat
- ✅ Has speaker icon for TTS

### Success Criteria:
- [ ] Each student has unique color
- [ ] Current user is always blue
- [ ] Colors are consistent per user
- [ ] Moderator is always yellow

### If Failed:
- Check `getUserColor()` function in ChatRoom.js
- Verify USER_COLORS array exists
- Check Tailwind CSS classes are applied

---

## Test 7: Active Mode AI Moderation ⭐⭐⭐

**Tests if AI moderator responds intelligently**

### Steps:
1. Open `http://localhost:3000/join/active`
2. Wait for story to start
3. **Send a message**: "What is this story about?"
4. **Stop typing** and wait 20 seconds

### Expected Results:

**After 20 seconds of silence:**
- ✅ Moderator sends an AI-generated message
- ✅ Message is contextual (related to story or your question)
- ✅ Examples:
  - "Great question! The story is about..."
  - "What do you think happens next?"
  - "Let me continue the story..."

### Check Backend Logs:
```
🔕 Silence detected (20s)
🤖 Generating moderator response...
💬 Moderator: "Great question! The story is about..."
```

### Success Criteria:
- [ ] Moderator responds after 20 seconds of silence
- [ ] Response is relevant to conversation
- [ ] Response uses GPT-4o-mini (contextual, not random)
- [ ] Story advances OR question is asked

### If Failed:
- Check `ACTIVE_SILENCE_SECONDS` setting (should be 20)
- Verify OpenAI API key in `.env`
- Check `check_silence()` function in app.py
- Look for errors in backend logs

---

## Test 8: Passive Mode Auto-Advance ⭐⭐

**Tests if story auto-advances on timer**

### Steps:
1. Open `http://localhost:3000/join/passive`
2. Wait and observe
3. Do NOT send any messages

### Expected Results:

**Every 10 seconds:**
- ✅ New story chunk appears automatically
- ✅ No AI questions or interventions
- ✅ Story keeps advancing regardless of chat activity

**Timeline:**
```
0s  - Welcome message
10s - Story chunk 1
20s - Story chunk 2
30s - Story chunk 3
...continues until story ends
```

### Check Backend Logs:
```
📖 Story chunk sent to [room-id]: "Once upon a time..."
📖 Story chunk sent to [room-id]: "The princess found..."
📖 Story chunk sent to [room-id]: "She opened the door..."
```

### Success Criteria:
- [ ] Story advances every 10 seconds
- [ ] No AI intervention during story
- [ ] Timer-based, not chat-based
- [ ] Students can chat freely between chunks

### If Failed:
- Check `STORY_CHUNK_INTERVAL` setting (should be 10)
- Verify passive mode is selected
- Check `send_next_chunk()` function

---

## Test 9: Room Deletion ⭐

### Steps:
1. Create a room (open `/join/active`)
2. Go to Admin Panel → Rooms tab
3. Find the room in the list
4. Click "Delete" button
5. Confirm deletion

### Expected Results:
- ✅ Confirmation dialog appears: "Are you sure you want to delete this room?"
- ✅ After confirming: "✅ Room deleted successfully"
- ✅ Room disappears from list
- ✅ Refresh page - room still gone

### Check Database:
```bash
# In Supabase Dashboard → Table Editor → rooms
# Verify the room is no longer there
```

### Check Backend Logs:
```
🗑️ Admin: Deleted room [room-id]
```

### Success Criteria:
- [ ] Delete button works
- [ ] Confirmation dialog appears
- [ ] Room is removed from database
- [ ] Associated data deleted (messages, participants)

### If Failed:
- Check DELETE endpoint in admin_api.py
- Verify foreign key constraints in database
- Check Supabase permissions

---

## Test 10: Settings Editor ⭐⭐

### Steps:
1. Go to Admin Panel → Settings tab
2. Find `ACTIVE_STORY_STEP`
3. Click "Edit"
4. Change value from `1` to `2`
5. Click "Save"
6. Restart backend server
7. Create new room and test

### Expected Results:

**Before Change:**
- Story sends 1 sentence per chunk

**After Change:**
- Story sends 2 sentences per chunk

**Admin Panel:**
- ✅ Alert shows: "✅ Setting 'ACTIVE_STORY_STEP' updated successfully. Restart backend to apply."
- ✅ New value shows in settings table
- ✅ Change persists after page refresh

### Check Database:
```sql
-- In Supabase SQL Editor
SELECT * FROM settings WHERE key = 'ACTIVE_STORY_STEP';
-- Should show value = '2'
```

### Success Criteria:
- [ ] Edit mode works
- [ ] Value saves to database
- [ ] Change persists after refresh
- [ ] Backend loads new value on restart

### If Failed:
- Check PUT endpoint in admin_api.py
- Verify settings table in Supabase
- Check `get_setting_value()` function

---

## Test 11: Personalized Feedback ⭐⭐⭐

**Tests if feedback appears at story end**

### Steps:
1. Open `http://localhost:3000/join/active`
2. Participate in the story (send 3-5 messages)
3. Wait for entire story to complete

**Important**: Stories are long! To test faster:
- Go to Admin Panel → Settings
- Change `ACTIVE_STORY_STEP` to `10` (sends 10 sentences at once)
- Restart backend
- Story will finish much faster

### Expected Results:

**When story ends:**
- ✅ Moderator sends: "✨ We have reached the end of the story."
- ✅ Page automatically redirects to `/feedback`
- ✅ Feedback page shows YOUR personalized feedback
- ✅ Feedback mentions specific things you said
- ✅ Feedback highlights strengths and suggestions

**Example Feedback:**
```
Great job, Student 123!

Strengths:
- You asked thoughtful questions about the princess
- You participated actively throughout the story

Areas for Improvement:
- Try to elaborate more on your answers
- Consider connecting ideas to real-life situations

Overall: Excellent participation!
```

### Check Backend Logs:
```
✨ Story complete for room [room-id]
🎯 Generating personalized feedback...
📝 Feedback generated for Student 123
```

### Success Criteria:
- [ ] Story completes successfully
- [ ] Redirect to feedback page happens automatically
- [ ] Feedback is personalized (uses your messages)
- [ ] Feedback makes sense contextually

### If Failed:
- Check `end_story()` function in app.py
- Verify `generate_personalized_feedback()` function
- Check OpenAI API for feedback generation
- Look for redirect in ChatRoom.js

---

## Test 12: Database Persistence ⭐

**Tests if data survives backend restart**

### Steps:
1. Create a room with 2 users
2. Send 5 messages in chat
3. Note the Room ID
4. **Stop backend** (Ctrl+C in terminal)
5. **Restart backend** (`python app.py`)
6. Go to Admin Panel → Rooms tab
7. Find the room by Room ID
8. Click "View" to see details

### Expected Results:
- ✅ Room still exists in database
- ✅ All 5 messages are preserved
- ✅ Participant information intact
- ✅ Room status unchanged

### Check Database Directly:
```sql
-- In Supabase SQL Editor
SELECT * FROM rooms WHERE id = 'your-room-id';
SELECT * FROM messages WHERE room_id = 'your-room-id';
SELECT * FROM participants WHERE room_id = 'your-room-id';
```

### Success Criteria:
- [ ] Data persists after backend restart
- [ ] No data loss
- [ ] Can view historical conversations
- [ ] All tables have data

### If Failed:
- Check Supabase connection
- Verify data is being written (check during creation)
- Check database migrations ran correctly

---

## Test 13: Export Research Data ⭐

### Steps:
1. Create 2-3 completed sessions
2. Use curl or browser:
```bash
curl http://localhost:5000/admin/export/sessions > sessions.json
```
3. Open `sessions.json`

### Expected Results:
- ✅ JSON file with array of sessions
- ✅ Each session has:
  - Room ID
  - Mode (active/passive)
  - Participant count
  - Message count
  - Duration
  - Started/ended timestamps
  - Story ID

### Success Criteria:
- [ ] Export endpoint works
- [ ] JSON is valid format
- [ ] Contains all session data
- [ ] Useful for research analysis

---

## 🔍 Common Issues & Solutions

### Issue: "Cannot connect to backend"
**Check:**
- [ ] Backend running on port 5000
- [ ] No firewall blocking
- [ ] CORS enabled in app.py

### Issue: "Room not loading"
**Check:**
- [ ] Room exists in database
- [ ] Username is in URL params
- [ ] WebSocket connection established

### Issue: "Story not starting"
**Check:**
- [ ] `ENABLE_AUTO_START_SINGLE_USER` setting
- [ ] Participant count meets minimum
- [ ] Story files exist in `server/stories/`

### Issue: "Moderator not responding"
**Check:**
- [ ] Active mode selected
- [ ] OpenAI API key valid
- [ ] Silence timer working (20 seconds)
- [ ] Backend logs for AI errors

### Issue: "Settings not saving"
**Check:**
- [ ] Database migrations ran
- [ ] Settings table exists
- [ ] Backend restarted after change

---

## ✅ Quick Test Summary

**Minimum tests to verify everything works:**

1. [ ] Admin panel loads (`http://localhost:3000/admin`)
2. [ ] Can copy shareable links
3. [ ] Auto-join works (3 users fill same room)
4. [ ] Each user has different color in chat
5. [ ] Active mode: AI responds after 20s silence
6. [ ] Passive mode: Story auto-advances every 10s
7. [ ] Can delete rooms from admin panel
8. [ ] Can edit settings and they persist
9. [ ] Feedback appears at story end
10. [ ] Data persists after backend restart

**If all 10 pass: ✅ Your project is fully working!**

---

## 📊 Testing Progress Tracker

Mark as you complete:

**Setup:**
- [ ] Backend running without errors
- [ ] Frontend running without errors
- [ ] Database connection working
- [ ] Admin panel accessible

**Core Features:**
- [ ] Shareable links work
- [ ] Auto room assignment works
- [ ] Multi-user room filling works
- [ ] Color-coded chat works
- [ ] Room deletion works
- [ ] Settings editor works

**AI Features:**
- [ ] Active mode AI responds
- [ ] Passive mode auto-advances
- [ ] Personalized feedback generates
- [ ] Story loading works

**Data:**
- [ ] Database persistence works
- [ ] Export data works
- [ ] Admin logs track actions

---

## 🎯 Advanced Testing

If you want to be thorough:

### Load Testing:
- [ ] 10+ simultaneous users
- [ ] Multiple concurrent rooms
- [ ] Long stories (100+ chunks)

### Edge Cases:
- [ ] User disconnects mid-story
- [ ] Empty messages
- [ ] Very long messages
- [ ] Special characters in username

### Cross-Browser:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

---

**Need help with any failing test? Let me know which test number failed and what error you see!**
