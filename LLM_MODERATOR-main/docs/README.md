# Documentation Index

Welcome to the LLM Moderator documentation! This directory contains all project documentation organized by topic.

---

## Quick Navigation

| Document | Description | Audience |
|----------|-------------|----------|
| [**Quick Start**](QUICK_START.md) | Get running in 10 minutes | Everyone |
| [**Implementation Plan**](IMPLEMENTATION_PLAN.md) | Roadmap for Supabase integration | Developers |
| [**Development Setup**](setup/DEVELOPMENT_SETUP.md) | Complete setup guide | New developers |
| [**Supabase Setup**](setup/SUPABASE_SETUP.md) | Database configuration | Backend developers |
| [**System Overview**](architecture/SYSTEM_OVERVIEW.md) | Architecture & design | All developers |
| [**Database Schema**](architecture/database-schema.md) | Database structure | Backend/Data team |

---

## Documentation Structure

```
docs/
├── README.md                      # This file - documentation index
├── QUICK_START.md                 # 10-minute setup guide
├── IMPLEMENTATION_PLAN.md         # Development roadmap
│
├── setup/                         # Setup guides
│   ├── DEVELOPMENT_SETUP.md       # Full local development setup
│   └── SUPABASE_SETUP.md          # Database setup instructions
│
├── architecture/                  # System design docs
│   ├── SYSTEM_OVERVIEW.md         # High-level architecture
│   └── database-schema.md         # Database design & tables
│
└── api/                           # API documentation (future)
    └── README.md                  # API endpoints reference
```

---

## Getting Started Paths

### I'm New to This Project
1. Read [Quick Start](QUICK_START.md) to get running
2. Skim [System Overview](architecture/SYSTEM_OVERVIEW.md) to understand architecture
3. Follow [Development Setup](setup/DEVELOPMENT_SETUP.md) for detailed setup

### I'm Working on Backend
1. Read [Supabase Setup](setup/SUPABASE_SETUP.md)
2. Review [Database Schema](architecture/database-schema.md)
3. Check [Implementation Plan](IMPLEMENTATION_PLAN.md) for tasks
4. Reference SQL files in `../supabase/queries/`

### I'm Working on Frontend
1. Read [Quick Start](QUICK_START.md)
2. Review [System Overview](architecture/SYSTEM_OVERVIEW.md)
3. Check [Implementation Plan](IMPLEMENTATION_PLAN.md) Phase 2

### I'm Setting Up Database
1. Follow [Supabase Setup](setup/SUPABASE_SETUP.md) step-by-step
2. Read [Database Schema](architecture/database-schema.md)
3. Run migrations from `../supabase/migrations/`

### I'm Researching/Analyzing Data
1. Read [Database Schema](architecture/database-schema.md)
2. Review SQL queries in `../supabase/queries/`
3. Follow data export instructions (coming soon)

---

## Key Concepts

### Moderation Modes
- **Active Mode**: AI actively engages, asks questions, story advances on participation
- **Passive Mode**: Story auto-advances at intervals, minimal AI interaction

### Auto Room Assignment
- Users click `/join/active` or `/join/passive` links
- System automatically assigns to available room (max 3 participants)
- New room created if all existing rooms are full

### Anonymous Participation
- No login required
- Auto-generated names: "Student 1", "Student 2", etc.
- All data stored for research purposes

### Data Flow
1. User joins via link
2. Backend assigns to room in Supabase
3. Real-time chat via Socket.IO
4. All messages stored in database
5. Session tracked for research analysis

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Socket.IO Client + Tailwind CSS |
| Backend | Python Flask + Flask-SocketIO |
| Database | Supabase (PostgreSQL) |
| AI | OpenAI GPT-4o-mini + LangChain |
| Deployment | TBD (Docker recommended) |

---

## Development Workflow

1. **Setup**: Follow [Development Setup](setup/DEVELOPMENT_SETUP.md)
2. **Work**: Create feature branch, make changes
3. **Test**: Manual testing + database verification
4. **Document**: Update docs if architecture changes
5. **Review**: Create PR, get team review
6. **Merge**: Squash and merge to main

---

## Common Tasks

### Adding a New Feature
1. Check [Implementation Plan](IMPLEMENTATION_PLAN.md) for roadmap
2. Create feature branch: `git checkout -b feature/name`
3. Update relevant code
4. Test thoroughly
5. Update documentation if needed
6. Create PR

### Modifying Database Schema
1. Create new migration file: `supabase/migrations/00X_description.sql`
2. Test in Supabase SQL Editor
3. Update [Database Schema](architecture/database-schema.md) docs
4. Update `supabase_client.py` if needed
5. Document in PR

### Troubleshooting
1. Check [Quick Start](QUICK_START.md) troubleshooting section
2. Review [Development Setup](setup/DEVELOPMENT_SETUP.md) common issues
3. Search GitHub issues
4. Ask team in chat
5. Create GitHub issue if new problem

---

## Contributing to Documentation

### When to Update Docs
- Adding new features
- Changing architecture
- Modifying database schema
- Discovering new setup steps
- Solving common problems

### How to Update
1. Edit relevant markdown file
2. Keep formatting consistent
3. Add examples where helpful
4. Update this index if adding new docs
5. Include in PR

### Documentation Standards
- Use clear, concise language
- Include code examples
- Add troubleshooting tips
- Keep structure organized
- Use tables and lists for readability

---

## Related Files

Outside of `docs/`:
- `../README.md` - Main project README
- `../supabase/migrations/` - Database migration files
- `../supabase/queries/` - SQL query reference
- `../server/supabase_client.py` - Database operations code

---

## Questions?

If you can't find what you're looking for:
1. Search all docs files (use IDE search)
2. Check code comments in relevant files
3. Review Supabase queries in `../supabase/queries/`
4. Ask team members
5. Create GitHub issue to request doc improvement

---

## Document Maintenance

This documentation should be reviewed and updated:
- ✅ When adding new features
- ✅ When changing architecture
- ✅ After major milestones
- ✅ When developers report confusion

**Last Updated**: 2026-01-03
**Maintained By**: Development Team
