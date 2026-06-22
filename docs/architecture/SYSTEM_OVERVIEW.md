# System Architecture Overview

## High-Level Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  React Frontend │◄───────►│  Flask Backend   │◄───────►│    Supabase     │
│   (Port 3000)   │         │   (Port 5000)    │         │   (PostgreSQL)  │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │
        │                            │
        │    Socket.IO (WebSocket)   │
        └────────────────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │                  │
                            │   OpenAI API     │
                            │  (GPT-4o-mini)   │
                            │                  │
                            └──────────────────┘
```

---

## Component Breakdown

### 1. Frontend (React SPA)

**Technology**: React 18, Socket.IO Client, Tailwind CSS

**Responsibilities**:
- User interface for room creation/joining
- Real-time chat interface
- Story progression display
- Moderator message rendering

**Key Files**:
- `App.js` - Main routing and app structure
- `RoomCreation.js` - Create/join room interface
- `ChatRoom.js` - Main chat interface
- `socket.js` - Socket.IO client configuration

**Communication**:
- HTTP requests for initial page load
- WebSocket (Socket.IO) for real-time chat

---

### 2. Backend (Flask + Socket.IO)

**Technology**: Python 3.11+, Flask, Flask-SocketIO, Supabase Client

**Responsibilities**:
- WebSocket server for real-time communication
- Room management and auto-assignment
- AI moderation logic (active/passive modes)
- Database operations via Supabase
- Story loading and progression
- TTS/STT endpoints

**Key Files**:
- `app.py` - Main server, Socket.IO events
- `supabase_client.py` - Database operations
- `prompts.py` - AI prompt templates
- `chatbot.py` - OpenAI API wrapper
- `data_retriever.py` - Story management

**Communication**:
- Socket.IO events with frontend
- HTTP requests to Supabase
- HTTP requests to OpenAI API

---

### 3. Database (Supabase/PostgreSQL)

**Technology**: PostgreSQL 15+ (hosted on Supabase)

**Responsibilities**:
- Persistent storage of all conversations
- Room and participant management
- Session tracking
- Research data exports

**Tables**:
- `rooms` - Chat room metadata
- `participants` - Anonymous users
- `messages` - All chat messages
- `sessions` - Completed conversations
- `research_data` - Exported data

**Features**:
- Automatic triggers for participant counting
- JSONB metadata for flexible analytics
- Indexes for fast queries

---

### 4. AI Layer (OpenAI)

**Technology**: OpenAI GPT-4o-mini, LangChain

**Responsibilities**:
- Content moderation
- Story advancement suggestions
- Question generation (active mode)
- Intervention decisions

**Modes**:
- **Active Mode**: AI actively engages, asks questions
- **Passive Mode**: AI passively narrates, story auto-advances

---

## Data Flow

### User Joins Room

```
1. User opens frontend (localhost:3000)
2. Clicks "Join Active/Passive"
3. Frontend → Backend: HTTP request /join/{mode}
4. Backend → Supabase: find_available_room(mode)
5. If no room: create_room(mode)
6. Backend → Frontend: room_id
7. Frontend redirects to /chat/{room_id}
8. Frontend → Backend: Socket.IO connect + join_room event
9. Backend → Supabase: add_participant(room_id, auto_name, socket_id)
10. Backend → Supabase: get_chat_history(room_id)
11. Backend → Frontend: chat_history event
12. User sees chat interface with history
```

### User Sends Message

```
1. User types message in frontend
2. Frontend → Backend: send_message event (via Socket.IO)
3. Backend → Supabase: add_message(room_id, sender, message)
4. Backend → All clients in room: receive_message event
5. All users see the message in real-time

[Active Mode Only]
6. Backend checks: should AI intervene?
7. If yes → OpenAI API: generate_moderator_reply()
8. Backend → Supabase: add_message(room_id, "Moderator", ai_reply)
9. Backend → All clients: receive_message event (Moderator)
10. Backend → Supabase: update_story_progress()
```

### Story Progression

**Active Mode**:
- Story advances when students participate
- Triggered by silence monitor (if no activity for X seconds)
- AI generates contextual response + next story chunk

**Passive Mode**:
- Story auto-advances every X seconds
- Background task runs continuously
- No AI questions, just narration

### Session End

```
1. Story reaches final sentence
2. Backend → Supabase: update_room_status(completed)
3. Backend → Supabase: end_session(room_id)
4. Backend → All clients: story_completed event
5. Frontend shows feedback/completion page
6. Supabase calculates session statistics (duration, messages, etc.)
```

---

## Auto Room Assignment Logic

**Current Implementation (To Be Added)**:

```python
def handle_join_request(mode):
    # Find room with space
    room = find_available_room(mode)

    if not room:
        # Create new room if none available
        room = create_room(mode)

    # Generate anonymous name
    participant_name = get_next_participant_name(room.id)

    # Add participant
    add_participant(room.id, participant_name, socket_id)

    # Start story when 2+ participants
    if room.current_participants >= 2:
        start_story(room)

    return room
```

**URL Structure**:
- `/join/active` → Auto-assigns to active mode room
- `/join/passive` → Auto-assigns to passive mode room
- `/room/{room_id}` → Direct room access (for reconnection)

---

## Moderation Modes

### Active Mode

**Behavior**:
- AI actively participates in conversation
- Asks comprehension questions
- Provides hints and encouragement
- Story advances when students engage
- Silence monitor triggers interventions

**Use Case**: Structured learning, guided discussion

### Passive Mode

**Behavior**:
- AI narrates story automatically
- Story advances on fixed intervals (e.g., every 10 seconds)
- Minimal AI intervention
- Students can still chat freely

**Use Case**: Independent reading, less structured

---

## Security & Privacy

### Anonymous Participation
- No user accounts required
- Auto-generated names ("Student 1", "Student 2")
- No personal data collected

### Data Protection
- Supabase Service Key stored server-side only
- OpenAI API key never exposed to frontend
- CORS configured for localhost (dev) / specific domain (prod)

### Research Ethics
- All conversations stored for research
- Participants aware of data collection (informed consent)
- Data exported in anonymized format

---

## Scalability Considerations

### Current Limitations
- In-memory Socket.IO connections (single server)
- No horizontal scaling (yet)
- Suitable for small-medium studies (<100 concurrent users)

### Future Improvements
- Redis adapter for Socket.IO (multi-server support)
- Load balancer for backend instances
- Connection pooling for Supabase
- CDN for frontend assets

---

## Development vs Production

### Development
- Frontend: `npm start` (localhost:3000)
- Backend: `python app.py` (localhost:5000)
- Database: Supabase free tier
- CORS: Allow all origins

### Production
- Frontend: Static build served via Nginx/Vercel/Netlify
- Backend: Gunicorn + Nginx reverse proxy
- Database: Supabase pro tier (backups enabled)
- CORS: Restricted to frontend domain
- SSL/HTTPS required

---

## Monitoring & Analytics

### Operational Monitoring
- Backend logs: `server_debug.log`
- Room logs: `room-{id}.log`
- Supabase dashboard: Query performance

### Research Analytics
- Session duration tracking
- Message frequency analysis
- AI intervention patterns
- Student participation rates

All analytics queries available in `supabase/queries/session_queries.sql`

---

## Technology Choices Rationale

| Choice | Reason |
|--------|--------|
| **Flask** | Lightweight, easy to integrate with Socket.IO |
| **Socket.IO** | Reliable WebSocket library with fallbacks |
| **React** | Modern UI framework, great for real-time updates |
| **Supabase** | PostgreSQL-based, easy setup, free tier, research-friendly |
| **OpenAI** | State-of-art language models, simple API |
| **LangChain** | Prompt management, reusable AI patterns |

---

## Next Steps

1. Implement auto room assignment (`/join/{mode}` endpoints)
2. Update Flask app to use Supabase instead of in-memory storage
3. Add session tracking and analytics
4. Deploy to production environment
5. Set up monitoring and backups
