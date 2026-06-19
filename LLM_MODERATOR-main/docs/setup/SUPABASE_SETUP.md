# Supabase Setup Guide

This guide will help you set up Supabase for the LLM Moderator project.

## Prerequisites

- Supabase account (free tier is sufficient for development)
- PostgreSQL knowledge (basic)

---

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Create a new organization (if you don't have one)
4. Click "New Project"
5. Fill in project details:
   - **Name**: `llm-moderator` (or your preference)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is fine for development

6. Click "Create new project"
7. Wait 2-3 minutes for project setup

---

## Step 2: Get API Credentials

Once your project is ready:

1. Go to **Project Settings** (gear icon in sidebar)
2. Navigate to **API** section
3. Copy the following values:

   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **Service Role Key**: `eyJhbGc...` (long token)

⚠️ **IMPORTANT**: The Service Role Key bypasses Row Level Security - keep it secret!

---

## Step 3: Configure Environment Variables

Create/update `server/.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# OpenAI Configuration (existing)
OPENAI_API_KEY=your-openai-api-key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1500
```

⚠️ **Never commit `.env` to git!** It's already in `.gitignore`.

---

## Step 4: Run Database Migrations

### Option A: Using Supabase Dashboard (Recommended for First Time)

1. Go to **SQL Editor** in Supabase dashboard
2. Click "New Query"
3. Copy the contents of `supabase/migrations/001_initial_schema.sql`
4. Paste into the SQL editor
5. Click "Run" (or press `Ctrl+Enter`)
6. You should see: "Success. No rows returned"

### Option B: Using Supabase CLI (Advanced)

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-id

# Run migrations
supabase db push
```

---

## Step 5: Verify Database Setup

1. Go to **Table Editor** in Supabase dashboard
2. You should see these tables:
   - `rooms`
   - `participants`
   - `messages`
   - `sessions`
   - `research_data`

3. Click on each table to verify columns match the schema

---

## Step 6: Test Connection

From your `server/` directory:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR: venv\Scripts\activate  # Windows

# Install dependencies (including supabase)
pip install -r requirements.txt

# Test connection
python -c "from supabase_client import supabase; print('✅ Supabase connected!')"
```

If you see "✅ Supabase connected!" - you're good to go!

---

## Step 7: Enable Realtime (Optional)

For real-time database updates (advanced feature):

1. Go to **Database** → **Replication**
2. Enable replication for tables you want to subscribe to:
   - `messages` (for real-time chat updates)
   - `participants` (for user join/leave events)

---

## Common Issues & Troubleshooting

### Issue: "Missing Supabase credentials"

**Solution**: Make sure `.env` file exists in `server/` directory with correct values.

### Issue: "Connection refused"

**Solution**:
- Check SUPABASE_URL is correct (no trailing slash)
- Verify project is active in Supabase dashboard
- Check internet connection

### Issue: "Permission denied" on queries

**Solution**:
- Ensure you're using SUPABASE_SERVICE_KEY (not anon key)
- Verify RLS is disabled (see migration file)

### Issue: Migration fails with "relation already exists"

**Solution**:
- Drop existing tables in SQL Editor:
  ```sql
  DROP TABLE IF EXISTS research_data CASCADE;
  DROP TABLE IF EXISTS sessions CASCADE;
  DROP TABLE IF EXISTS messages CASCADE;
  DROP TABLE IF EXISTS participants CASCADE;
  DROP TABLE IF EXISTS rooms CASCADE;
  ```
- Re-run migration

---

## Security Best Practices

1. ✅ **Never expose Service Role Key** - only use server-side
2. ✅ **Use environment variables** - never hardcode credentials
3. ✅ **Enable backups** - configure in Supabase dashboard
4. ✅ **Monitor usage** - check Supabase dashboard regularly
5. ✅ **Rotate keys periodically** - especially before production

---

## Next Steps

- Read [Database Schema Documentation](../architecture/database-schema.md)
- Review [API Documentation](../api/README.md)
- See [Deployment Guide](DEPLOYMENT.md) for production setup

---

## Useful Supabase Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Guide](https://supabase.com/docs/guides/database)
- [Python Client Docs](https://supabase.com/docs/reference/python/introduction)
- [Community Discord](https://discord.supabase.com)
