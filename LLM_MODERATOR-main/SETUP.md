# LLM Moderator - Complete Setup Guide

Complete step-by-step guide to set up and run the LLM Moderator platform with Supabase database and admin panel.

---

## Overview

This platform is a collaborative learning system with:
- **Flask Backend** with Socket.IO for real-time chat
- **React Frontend** with Tailwind CSS
- **Supabase PostgreSQL Database** for data persistence
- **Admin Panel** for managing settings and monitoring rooms
- **OpenAI GPT-4o-mini** for AI moderation

---

## Prerequisites

Before starting, ensure you have:

1. **Python 3.11+** installed
2. **Node.js 16+** and **npm** installed
3. **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
4. **Supabase Account** ([Sign up here](https://supabase.com))
5. **FFmpeg** (optional, for audio features)

---

## Step 1: Supabase Database Setup

### 1.1 Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Click "New Project"
3. Fill in:
   - **Project Name**: `llm-moderator` (or your choice)
   - **Database Password**: Save this securely!
   - **Region**: Choose closest to you
4. Click "Create new project"
5. Wait 2-3 minutes for setup to complete

### 1.2 Get Database Credentials

1. In your Supabase project dashboard, click **Settings** (gear icon) → **API**
2. Copy the following values:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **Project API keys** → **service_role** key (NOT the anon key)

### 1.3 Run Database Migrations

1. In Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **"New query"**
3. Open `supabase/migrations/001_initial_schema.sql` from this repo
4. Copy the entire contents and paste into SQL Editor
5. Click **"Run"** (or press Cmd/Ctrl + Enter)
6. Verify success: You should see "Success. No rows returned"

7. **Repeat for admin settings migration**:
   - Click **"New query"** again
   - Open `supabase/migrations/002_admin_settings.sql`
   - Copy contents and paste
   - Click **"Run"**
   - Verify success

8. **Verify tables created**:
   - Go to **Table Editor** (left sidebar)
   - You should see tables: `rooms`, `participants`, `messages`, `sessions`, `research_data`, `settings`, `admin_logs`

---

## Step 2: Backend Setup

### 2.1 Create Environment File

1. Navigate to the `server/` directory
2. Create a file named `.env`
3. Add the following configuration:

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1500

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Server Configuration
FLASK_PORT=5000
FLASK_HOST=0.0.0.0

# Feature Flags
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_AUTO_START_SINGLE_USER=true

# Room Configuration
MAX_PARTICIPANTS_PER_ROOM=3
ROOM_IDLE_TIMEOUT_MINUTES=60

# Moderation Modes
ACTIVE_MODE=active
PASSIVE_MODE=passive

# Story Progression
ACTIVE_STORY_STEP=1
PASSIVE_STORY_STEP=1
STORY_CHUNK_INTERVAL=10

# Silence/Intervention Windows (seconds)
ACTIVE_SILENCE_SECONDS=20
PASSIVE_SILENCE_SECONDS=10
ACTIVE_INTERVENTION_WINDOW_SECONDS=20
PASSIVE_INTERVENTION_WINDOW_SECONDS=10

# Messages
WELCOME_MESSAGE=Welcome everyone! I'm the Moderator.
ACTIVE_ENDING_MESSAGE=✨ We have reached the end of the story.
PASSIVE_ENDING_MESSAGE=✨ We have reached the end of the story.

# Ending Styles
ACTIVE_ENDING_STYLE=warm
PASSIVE_ENDING_STYLE=warm

# Chat History Limit
CHAT_HISTORY_LIMIT=50
```

**IMPORTANT**: Replace these placeholders:
- `https://your-project.supabase.co` → Your Supabase Project URL
- `your_service_role_key_here` → Your Supabase service role key
- `your_openai_api_key_here` → Your OpenAI API key

### 2.2 Install Python Dependencies

1. Open terminal and navigate to `server/` directory:
   ```bash
   cd server
   ```

2. Create virtual environment:
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify installation:
   ```bash
   pip list
   ```
   You should see packages like `Flask`, `Flask-SocketIO`, `supabase`, `openai`, etc.

### 2.3 Start Backend Server

1. With virtual environment activated, run:
   ```bash
   python app.py
   ```

2. **Verify successful startup**. You should see:
   ```
   ============================================================
   🚀 LLM Moderator Server Starting
   ============================================================
   ✅ Admin API registered at /admin
   📝 Loading configuration from database...
   📝 Config: Active Step=1, Passive Step=1
   📝 Config: Story Interval=10s
   📝 Frontend URL: http://localhost:3000
   ============================================================
   🚀 Starting Flask-SocketIO server
   📍 Host: 0.0.0.0:5000
   🌐 Frontend: http://localhost:3000
   ============================================================
   ```

3. **If you see errors**, check:
   - `.env` file exists in `server/` directory
   - Supabase credentials are correct
   - Database migrations were run successfully
   - OpenAI API key is valid

**Keep this terminal open**. The server must run for the frontend to work.

---

## Step 3: Frontend Setup

### 3.1 Install Node Dependencies

1. Open a **new terminal** (keep backend running)
2. Navigate to frontend directory:
   ```bash
   cd client/frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

   This will install: React, Socket.IO Client, Tailwind CSS, React Router, etc.

### 3.2 Start Frontend

1. Start the React development server:
   ```bash
   npm start
   ```

2. **Browser should auto-open** to `http://localhost:3000`
   - If not, manually open: [http://localhost:3000](http://localhost:3000)

3. **Verify frontend is running**:
   - You should see the room creation page
   - No console errors (check browser DevTools)

---

## Step 4: Test the System

### 4.1 Quick Test: Auto-Join

1. Open browser to: [http://localhost:3000/join/active](http://localhost:3000/join/active)
2. You should be automatically assigned to a room
3. Chat should load and show "waiting" or start the story

### 4.2 Test Multiple Users

1. **User 1**: [http://localhost:3000/join/active](http://localhost:3000/join/active)
2. **User 2**: Open same link in new tab/incognito window
3. **User 3**: Open same link in another tab

**Expected behavior**:
- All 3 users should join the **same room** (Room fills before creating new one)
- Story should start when first user joins (ENABLE_AUTO_START_SINGLE_USER=true)
- All users can see each other's messages in real-time

### 4.3 Test Admin Panel

1. Open: [http://localhost:3000/admin](http://localhost:3000/admin)
2. You should see:
   - **Dashboard** tab: Statistics (rooms, sessions, messages)
   - **Rooms** tab: List of all rooms
   - **Settings** tab: All configuration settings
3. Click "View" on a room to see full conversation
4. Try editing a setting:
   - Go to Settings tab
   - Find "ACTIVE_STORY_STEP"
   - Click "Edit"
   - Change value to "2"
   - Click "Save"
   - **Restart backend** to apply (settings loaded on startup)

---

## Step 5: Verify Database

### 5.1 Check Data in Supabase

1. Go to Supabase Dashboard → **Table Editor**
2. Check tables have data:
   - **rooms**: Should see created rooms
   - **participants**: Should see joined users
   - **messages**: Should see chat messages
   - **settings**: Should see 13 configuration entries
3. Click on any table to view contents

---

## What You Have Now

✅ **Backend Server** running on port 5000
✅ **Frontend App** running on port 3000
✅ **Supabase Database** with all tables and settings
✅ **Admin Panel** accessible at `/admin`
✅ **Auto-join URLs** at `/join/active` and `/join/passive`
✅ **Real-time chat** with Socket.IO
✅ **AI Moderation** powered by GPT-4o-mini

---

## URLs Reference

| URL | Purpose |
|-----|---------|
| `http://localhost:3000` | Main app (room creation) |
| `http://localhost:3000/join/active` | Auto-join active mode room |
| `http://localhost:3000/join/passive` | Auto-join passive mode room |
| `http://localhost:3000/admin` | Admin panel |
| `http://localhost:5000` | Backend API |
| `http://localhost:5000/admin/stats` | Admin stats API |
| `http://localhost:5000/admin/settings` | Admin settings API |

---

## Key Features to Try

### 1. Active Mode
- Story advances when students are silent for 20 seconds
- AI moderator actively engages and asks questions
- URL: `http://localhost:3000/join/active`

### 2. Passive Mode
- Story auto-advances every 10 seconds
- Minimal AI intervention
- URL: `http://localhost:3000/join/passive`

### 3. Admin Panel Features
- **Dashboard**: Real-time statistics with auto-refresh
- **Rooms**: View all rooms, filter by status, see live conversations
- **Settings**: Edit all configuration without code changes
- **Live Monitoring**: Click "View" on any room to see messages

### 4. Shareable Links
- Share `/join/active` or `/join/passive` links
- Users auto-assigned anonymous names (Student 1, Student 2, etc.)
- Rooms fill to 3 students before creating new room

---

## Troubleshooting

### Backend won't start

**Issue**: Import errors or connection errors

**Solutions**:
1. Verify virtual environment is activated: `which python` should show `venv/bin/python`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check `.env` file exists in `server/` directory
4. Verify Supabase credentials with: `python -c "from supabase_client import supabase; print(supabase.table('settings').select('*').execute())"`

### Frontend won't connect

**Issue**: "Cannot connect to server" or CORS errors

**Solutions**:
1. Verify backend is running on port 5000
2. Check browser console for errors
3. Verify FRONTEND_URL in `.env` is `http://localhost:3000`
4. Clear browser cache and reload

### Database errors

**Issue**: "Table does not exist" or "Permission denied"

**Solutions**:
1. Verify migrations were run (check Supabase Table Editor)
2. Use **service_role** key, NOT anon key
3. Re-run migrations from Supabase SQL Editor
4. Check Supabase logs: Settings → Logs

### Story not starting

**Issue**: Room stays in "waiting" state

**Solutions**:
1. Check backend logs: `tail -f server/server_debug.log`
2. Look for "🎬 Starting story" message
3. Verify ENABLE_AUTO_START_SINGLE_USER=true in `.env`
4. Check Supabase `rooms` table for room status

### Admin panel not loading

**Issue**: Admin panel shows errors or blank

**Solutions**:
1. Verify backend admin API is running: `curl http://localhost:5000/admin/stats`
2. Check browser console for errors
3. Verify settings migration ran: Check Supabase `settings` table
4. Restart backend server

### Settings not updating

**Issue**: Changed setting in admin panel but no effect

**Solutions**:
1. Verify setting saved in Supabase `settings` table
2. **Restart backend** - settings are loaded on startup
3. Check backend logs for "📝 Loading configuration from database"

---

## Logs and Debugging

### Backend Logs

**Log file**: `server/server_debug.log`

**View logs**:
```bash
cd server
tail -f server_debug.log
```

**Log icons**:
- 🔗 HTTP endpoint called
- 🔌 WebSocket connection
- 🚪 User joining room
- 🎬 Story starting
- 📖 Story chunk sent
- 💬 Chat message
- ✅ Success
- ❌ Error

See `docs/LOGGING_GUIDE.md` for complete guide.

### Frontend Logs

**Browser console**:
- Right-click → Inspect → Console
- Look for Socket.IO connection status
- Check for API errors

---

## Next Steps

1. **Read the guides**:
   - `docs/ADMIN_PANEL_GUIDE.md` - Complete admin panel usage
   - `docs/LOGGING_GUIDE.md` - Understanding logs
   - `docs/TESTING_GUIDE.md` - Testing scenarios

2. **Customize settings**:
   - Go to Admin Panel → Settings
   - Adjust chunk sizes, timings, messages
   - Restart backend to apply changes

3. **Add more stories**:
   - Stories are in `server/stories/` directory
   - Add new JSON files in same format
   - System randomly selects from available stories

4. **Export research data**:
   - API: `curl http://localhost:5000/admin/export/sessions > data.json`
   - Or via Supabase Dashboard: Table Editor → Export

---

## Production Deployment Notes

For production deployment, you should:

1. **Security**:
   - Add authentication to admin panel
   - Use environment-based secrets (not .env files)
   - Restrict CORS to specific domains
   - Use HTTPS for all connections

2. **Database**:
   - Enable Row Level Security (RLS) in Supabase
   - Set up database backups
   - Monitor connection pool limits

3. **Performance**:
   - Use production build: `npm run build`
   - Serve static files with Nginx/CDN
   - Enable Redis for session storage
   - Configure autoscaling

4. **Monitoring**:
   - Set up error tracking (Sentry)
   - Configure log aggregation
   - Monitor OpenAI API usage
   - Track database performance

---

## Getting Help

- **Documentation**: See `docs/` directory for detailed guides
- **Logs**: Check `server/server_debug.log` for errors
- **Supabase**: Check Settings → Logs in dashboard
- **API Testing**: Use curl or Postman to test endpoints

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.
