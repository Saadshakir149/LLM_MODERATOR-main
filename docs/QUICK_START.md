# Quick Start Guide

Get the LLM Moderator project running in 10 minutes.

---

## Prerequisites

- Python 3.11+
- Node.js 16+
- Supabase account
- OpenAI API key

---

## 1. Clone & Install (3 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/LLM_MODERATOR.git
cd LLM_MODERATOR

# Backend setup
cd server
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup (new terminal)
cd client/frontend
npm install
```

---

## 2. Configure Supabase (5 minutes)

### Create Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Wait for setup (2-3 mins)

### Run Migration
1. Go to **SQL Editor** in Supabase dashboard
2. Click "New Query"
3. Copy contents of `supabase/migrations/001_initial_schema.sql`
4. Paste and click "Run"

### Get Credentials
1. Go to **Project Settings** → **API**
2. Copy:
   - Project URL
   - Service Role Key (not anon key!)

---

## 3. Environment Variables (1 minute)

Create `server/.env`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...your-key

# OpenAI
OPENAI_API_KEY=sk-your-key
```

---

## 4. Run Servers (1 minute)

**Terminal 1 (Backend):**
```bash
cd server
source venv/bin/activate
python app.py
```

**Terminal 2 (Frontend):**
```bash
cd client/frontend
npm start
```

---

## 5. Test (1 minute)

1. Open `http://localhost:3000`
2. Create room → Select Active Mode → Pick a story
3. Open second browser window
4. Join same room
5. Send messages between windows

✅ **Working!**

---

## Troubleshooting

### "Module not found: supabase"
```bash
cd server
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied: react-scripts"
```bash
cd client/frontend
chmod +x node_modules/.bin/react-scripts
npm start
```

### "Missing Supabase credentials"
- Check `server/.env` exists
- Verify SUPABASE_URL and SUPABASE_SERVICE_KEY are correct

---

## What's Next?

- **For Developers**: Read [Implementation Plan](IMPLEMENTATION_PLAN.md)
- **For Setup Help**: See [Development Setup](setup/DEVELOPMENT_SETUP.md)
- **For Architecture**: Read [System Overview](architecture/SYSTEM_OVERVIEW.md)
- **For Supabase Details**: See [Supabase Setup](setup/SUPABASE_SETUP.md)

---

## Project Structure

```
LLM_MODERATOR/
├── server/              # Python Flask backend
│   ├── app.py           # Main server
│   ├── supabase_client.py  # Database operations
│   └── .env             # YOUR CONFIG HERE
├── client/frontend/     # React frontend
│   └── src/
├── supabase/           # Database migrations & queries
└── docs/               # Documentation (you are here!)
```

---

## Common Commands

```bash
# Start backend
cd server && source venv/bin/activate && python app.py

# Start frontend
cd client/frontend && npm start

# Install new Python package
cd server && source venv/bin/activate && pip install package-name

# Install new npm package
cd client/frontend && npm install package-name

# Check Supabase connection
cd server && python -c "from supabase_client import supabase; print('OK')"
```

---

## Need Help?

1. Check `docs/setup/DEVELOPMENT_SETUP.md`
2. Search GitHub issues
3. Ask your team
4. Create new issue with error details

---

## Current Status

✅ **Working**: Basic chat with in-memory storage
❌ **In Progress**: Supabase integration (see IMPLEMENTATION_PLAN.md)
❌ **Planned**: Auto room assignment via `/join/{mode}` links

Follow the [Implementation Plan](IMPLEMENTATION_PLAN.md) to complete the Supabase integration.
