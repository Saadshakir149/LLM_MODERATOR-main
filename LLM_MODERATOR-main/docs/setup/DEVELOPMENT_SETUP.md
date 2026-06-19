# Development Setup Guide

Complete guide to set up the LLM Moderator project for local development.

## Overview

This project consists of:
- **Backend**: Python Flask server with Socket.IO (port 5000)
- **Frontend**: React application (port 3000)
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-4o-mini

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** and npm ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads/))
- **Supabase account** ([Sign up](https://supabase.com))
- **OpenAI API Key** ([Get one](https://platform.openai.com/api-keys))

---

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/LLM_MODERATOR.git
cd LLM_MODERATOR
```

---

## Step 2: Set Up Supabase

Follow the detailed guide: [Supabase Setup](SUPABASE_SETUP.md)

**Quick summary:**
1. Create Supabase project
2. Get API credentials (URL + Service Key)
3. Run database migration (`supabase/migrations/001_initial_schema.sql`)
4. Verify tables are created

---

## Step 3: Backend Setup

### 3.1 Navigate to Server Directory

```bash
cd server
```

### 3.2 Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask & Flask-SocketIO
- Supabase Python client
- OpenAI SDK
- LangChain
- And all other dependencies

### 3.4 Configure Environment Variables

Create `server/.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1500

# Server Configuration (Optional)
WELCOME_MESSAGE=Welcome everyone! I'm the Moderator.
ACTIVE_STORY_STEP=1
PASSIVE_STORY_STEP=1
PASSIVE_SILENCE_SECONDS=10
ACTIVE_SILENCE_SECONDS=20
STORY_CHUNK_INTERVAL=10
```

### 3.5 Test Backend

```bash
# Test Supabase connection
python -c "from supabase_client import supabase; print('✅ Supabase OK')"

# Test OpenAI connection
python -c "from chatbot import llm; print('✅ OpenAI OK')"

# Run server
python app.py
```

You should see:
```
🚀 Moderator server running (Ultra Debug Mode — FINAL)
 * Running on http://0.0.0.0:5000
```

Keep this terminal open.

---

## Step 4: Frontend Setup

### 4.1 Open New Terminal

Navigate to frontend directory:

```bash
cd client/frontend
```

### 4.2 Install Dependencies

```bash
npm install
```

This installs:
- React & React DOM
- React Router
- Socket.IO Client
- Tailwind CSS
- Framer Motion
- And all other dependencies

### 4.3 Configure Environment (Optional)

Create `client/frontend/.env` (if needed):

```bash
REACT_APP_API_URL=http://localhost:5000
```

*Note: Socket.IO connection is already configured in `src/socket.js`*

### 4.4 Start Development Server

```bash
npm start
```

Frontend will automatically open at `http://localhost:3000`

---

## Step 5: Verify Setup

### Backend Health Check

Visit `http://localhost:5000/` - you should see Flask is running.

### Frontend Health Check

Visit `http://localhost:3000` - you should see the room creation page.

### Full Integration Test

1. Open `http://localhost:3000` in two browser windows
2. Window 1: Click "Create Room" → Select "Active Mode" → Choose a story
3. Copy the room ID
4. Window 2: Enter the room ID → Click "Join Room"
5. Both windows should now be in the chat room
6. Send a message from Window 1 → Should appear in Window 2
7. Check Supabase dashboard → Messages table should have your message

✅ If all above works, setup is complete!

---

## Project Structure

```
LLM_MODERATOR/
├── server/                     # Backend (Python Flask)
│   ├── app.py                  # Main server entry point
│   ├── supabase_client.py      # Database operations
│   ├── prompts.py              # AI prompts & LangChain
│   ├── chatbot.py              # OpenAI wrapper
│   ├── data_retriever.py       # Story loading
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (create this)
│   └── stories/                # Cached stories
│
├── client/frontend/            # Frontend (React)
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   ├── socket.js           # Socket.IO client
│   │   └── components/         # React components
│   ├── package.json            # Node dependencies
│   └── .env                    # Frontend env vars (optional)
│
├── supabase/                   # Database
│   ├── migrations/             # SQL migrations
│   └── queries/                # SQL query reference
│
├── docs/                       # Documentation
│   ├── setup/                  # Setup guides (you are here!)
│   ├── architecture/           # Architecture docs
│   └── api/                    # API documentation
│
└── README.md                   # Project overview
```

---

## Development Workflow

### Running Both Servers

**Terminal 1 (Backend):**
```bash
cd server
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

**Terminal 2 (Frontend):**
```bash
cd client/frontend
npm start
```

### Making Database Changes

1. Create new migration file: `supabase/migrations/00X_description.sql`
2. Run migration in Supabase SQL Editor
3. Update `supabase_client.py` if needed
4. Update documentation

### Code Changes

- **Backend**: Changes auto-reload (Flask debug mode)
- **Frontend**: Changes auto-reload (React hot reload)
- **Database**: Run migration, then restart backend

---

## Common Issues

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'supabase'`

**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend permission denied

**Error**: `Permission denied: react-scripts`

**Solution**:
```bash
chmod +x node_modules/.bin/react-scripts
```

Or:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Database connection errors

**Error**: `Missing Supabase credentials`

**Solution**: Verify `.env` file exists in `server/` with correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Port already in use

**Error**: `Address already in use: 5000`

**Solution**:
```bash
# macOS/Linux
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

## Team Collaboration

### Before You Start Working

```bash
git pull origin main
cd server && source venv/bin/activate && pip install -r requirements.txt
cd ../client/frontend && npm install
```

### Sharing Your Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes...

# Commit
git add .
git commit -m "Clear description of changes"

# Push
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Next Steps

- Read [Architecture Documentation](../architecture/database-schema.md)
- Review [API Documentation](../api/README.md)
- See [Deployment Guide](DEPLOYMENT.md) for production

---

## Need Help?

1. Check existing documentation in `docs/`
2. Search closed GitHub issues
3. Ask team members
4. Create a new GitHub issue with:
   - What you tried
   - Error messages
   - Your environment (OS, Python version, etc.)
