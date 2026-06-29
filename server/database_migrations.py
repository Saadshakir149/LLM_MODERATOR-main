import os
import logging

logger = logging.getLogger("database_migrations")

def run_db_migrations():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not found, skipping database migrations.")
        return
    try:
        import psycopg2
        logger.info("Connecting to database to run moderator_interventions schema migrations...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        sql_queries = [
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS reason TEXT;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS research_question VARCHAR(20);",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS expected_effect TEXT;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS ranking_state_before JSONB;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS ranking_state_after JSONB;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS participant_response TEXT;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS latency_seconds DOUBLE PRECISION;",
            "ALTER TABLE moderator_interventions ADD COLUMN IF NOT EXISTS success BOOLEAN;"
        ]
        
        for query in sql_queries:
            try:
                cur.execute(query)
            except Exception as e:
                logger.error(f"Migration error for '{query}': {e}")
                conn.rollback()
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database migrations completed successfully.")
    except ImportError:
        logger.warning("psycopg2-binary not installed. Automatic database migrations skipped. Please run 'pip install psycopg2-binary' manually.")
    except Exception as e:
        logger.error(f"Database migrations failed: {e}")
